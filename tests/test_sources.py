import json
import tempfile
import unittest
from pathlib import Path
from atlas_sources.acquire import collect, snapshot_dir
from atlas_sources.discover import parse_family
from atlas_sources.normalize import table_nodes, graph_nodes, qa
from atlas_sources.registry import read_json, validate
from atlas_sources.compare import compare_nodes


def resource(**updates):
    row = {"id": "example", "source_id": "EXAMPLE", "edition": "2020", "filename": "source.csv",
           "url": "https://example.org/source.csv", "encoding": "utf-8-sig", "format": "csv",
           "role": "structure", "language": "en", "parser": "un_numeric",
           "rights": {"download": True, "local_processing": True, "redistribute": True,
                      "license": "test fixture", "evidence_url": "https://example.org/license"}}
    row.update(updates)
    return row


class FakeHTTP:
    def __init__(self, data):
        self.data, self.requests = data, 0

    def allowed(self, url):
        return {"url": "https://example.org/robots.txt", "result": "test", "allowed": True}

    def get(self, url):
        self.requests += 1
        return self.data, {"final_url": url, "http_status": 200, "content_type": "text/csv"}


class CollectionTests(unittest.TestCase):
    def test_drift_preserves_original_pin_and_both_snapshots(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, r = Path(tmp), resource()
            first = collect(root, [r], freeze=True, client=FakeHTTP(b"a,b\n01,original\n"))[0]
            second = collect(root, [r], refresh=True, freeze=True, client=FakeHTTP(b"a,b\n01,revised\n"))[0]
            self.assertEqual(second["status"], "drift")
            self.assertEqual(read_json(root / "data/resources.lock.json")[r["id"]]["sha256"], first["sha256"])
            self.assertEqual((root / first["path"]).read_bytes(), b"a,b\n01,original\n")
            self.assertTrue((root / second["path"]).is_file())
            client = FakeHTTP(b"must not be requested")
            self.assertEqual(collect(root, [r], client=client)[0]["status"], "cached")
            self.assertEqual(client.requests, 0)

    def test_corruption_is_not_silently_replaced(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, r = Path(tmp), resource()
            first = collect(root, [r], freeze=True, client=FakeHTTP(b"a,b\n01,x\n"))[0]
            (root / first["path"]).write_bytes(b"tampered")
            client = FakeHTTP(b"new content")
            result = collect(root, [r], client=client)[0]
            self.assertEqual(result["status"], "failed")
            self.assertIn("hash mismatch", result["error"])
            self.assertEqual(client.requests, 0)

    def test_unknown_rights_never_send_request(self):
        with tempfile.TemporaryDirectory() as tmp:
            r = resource()
            r["rights"]["local_processing"] = None
            client = FakeHTTP(b"data")
            result = collect(Path(tmp), [r], client=client)[0]
            self.assertEqual(result["status"], "blocked_rights")
            self.assertEqual(client.requests, 0)
            self.assertFalse((Path(tmp) / "data/raw").exists())

    def test_bad_payload_preserved_but_not_pinned(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, r = Path(tmp), resource()
            result = collect(root, [r], freeze=True, client=FakeHTTP(b"<html>Login required</html>"))[0]
            self.assertEqual(result["status"], "failed")
            self.assertTrue((root / result["path"]).is_file())
            self.assertEqual(read_json(root / "data/resources.lock.json"), {})

    def test_local_only_raw_is_outside_public_raw(self):
        r = resource()
        r["rights"]["redistribute"] = None
        self.assertIn("data/local/raw", str(snapshot_dir(Path("/tmp"), r, "abc")))

    def test_fresh_checkout_fetches_missing_pinned_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, r = Path(tmp), resource()
            first = collect(root, [r], freeze=True, client=FakeHTTP(b"a,b\n01,x\n"))[0]
            (root / first["path"]).unlink()
            client = FakeHTTP(b"a,b\n01,x\n")
            self.assertEqual(collect(root, [r], client=client)[0]["status"], "downloaded")
            self.assertEqual(client.requests, 1)

    def test_resource_id_cannot_be_reused_for_another_edition(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, r = Path(tmp), resource()
            collect(root, [r], freeze=True, client=FakeHTTP(b"a,b\n01,x\n"))
            r["edition"] = "2021"
            client = FakeHTTP(b"a,b\n01,x\n")
            self.assertEqual(collect(root, [r], client=client)[0]["status"], "failed")
            self.assertEqual(client.requests, 0)


class ParsingTests(unittest.TestCase):
    def test_numeric_prefixes_preserve_zero_and_all_rows(self):
        data = b'CPC Ver. 3.0  Code,CPC Ver. 3.0 Title\n0,Root\n01,Branch\n011,Leaf\n'
        nodes = table_nodes(data, resource())
        self.assertEqual([n["code"] for n in nodes], ["0", "01", "011"])
        self.assertEqual(nodes[2]["parents"], ["01"])
        self.assertIsNone(nodes[0]["definition"])
        self.assertEqual(qa(nodes)["levels"], {1: 1, 2: 1, 3: 1})

    def test_unexpected_header_and_malformed_row_fail(self):
        with self.assertRaises(ValueError):
            table_nodes(b'Code,Description\n01,wrong edition\n', resource())
        with self.assertRaises(ValueError):
            table_nodes(b'CPC Ver. 3.0  Code,CPC Ver. 3.0 Title\n01,one,extra\n', resource())

    def test_isic_divisions_attach_to_the_source_section(self):
        data = b'Code,Description\nA,First section\n01,Division\n011,Group\n0111,Class\nB,Next section\n05,Next division\n'
        nodes = table_nodes(data, resource(parser="un_isic", edition="Rev.4"))
        self.assertEqual(nodes[-1]["parents"], ["B"])
        self.assertEqual(qa(nodes)["orphan_parents"], [])
        with self.assertRaises(ValueError):
            table_nodes(data, resource(parser="un_isic", edition="Rev.5"))

    def test_fixed_width_dotted_codes(self):
        nodes = table_nodes(b'Code          Description\r\n01            Topic\r\n01.0          Group\r\n01.0.0        Class\r\n', resource(parser="un_dotted"))
        self.assertEqual(nodes[-1]["parents"], ["01.0"])
        self.assertEqual(qa(nodes)["node_count"], 3)

    def test_qa_reports_cycles_orphans_duplicates_and_multiple_parents(self):
        nodes = [{"code": "a", "parents": ["b", "missing"]}, {"code": "b", "parents": ["a"]},
                 {"code": "c", "parents": ["c"]}, {"code": "c", "parents": ["c"]}]
        result = qa(nodes)
        self.assertEqual(result["duplicate_codes"], ["c"])
        self.assertTrue(result["cycles"])
        self.assertTrue(result["orphan_parents"])
        self.assertEqual(result["polyhierarchy_nodes"], 1)

    def test_no_parents_in_occupation_file_means_no_invented_tree(self):
        nodes = table_nodes(b'O*NET-SOC Code,Title,Description\n11-1011.00,Example,An official fixture definition\n', resource(parser="onet_occupations"))
        self.assertEqual(nodes[0]["parents"], [])
        self.assertEqual(nodes[0]["definition_origin"], "official_file")

    def test_identical_code_and_label_never_produce_equivalence(self):
        result = compare_nodes([{"code": "01", "label": "Same", "definition": None}],
                               [{"code": "01", "label": "Same", "definition": "Different scope"}])
        self.assertEqual(result["shared_code_strings"], 1)
        self.assertEqual(result["shared_codes_with_both_definitions"], 0)
        self.assertFalse(result["semantic_equivalence_inferred"])

    def test_ctdl_unexpected_types_and_missing_members_fail(self):
        graph = {"@graph": [{"@type": "ceterms:Collection", "ceterms:hasMember": ["missing"]}]}
        with self.assertRaises(ValueError):
            graph_nodes(json.dumps(graph).encode())
        graph["@graph"].append({"@type": "an unexpected object"})
        with self.assertRaises(ValueError):
            graph_nodes(json.dumps(graph).encode())


class DiscoveryTests(unittest.TestCase):
    def test_linked_and_unlinked_candidates_remain_candidates(self):
        html = '<h5>A total number of 2 classifications</h5><ul><li>Unlinked item</li><li><a href="/unsd/classifications/Family/Detail/123">Linked item</a></li></ul><ul><li>Not a classification</li></ul>'
        rows, expected = parse_family(html)
        self.assertEqual(len(rows), expected)
        self.assertIsNone(rows[0]["official_detail_url"])
        self.assertEqual(rows[1]["verification_status"], "candidate")
        with self.assertRaises(ValueError):
            parse_family(html.replace('of 2', 'of 3'))

    def test_repository_preserves_original_candidates_and_valid_resource_versions(self):
        self.assertEqual(validate(Path(__file__).resolve().parents[1]), [])


if __name__ == "__main__":
    unittest.main()
