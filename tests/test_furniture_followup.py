import copy
import json
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from atlas_sources.acquire import snapshot_dir
from atlas_sources.furniture import validate_slice
from atlas_sources.furniture_followup import (SKOS, XKOS, RDF_TYPE, NACE2, UN4, CURRENT,
    nace_code, rdf_nodes, reverse_correspondence, xkos_correspondence, direct_audit,
    compare_publisher_pairs, check_queries, extend_plan, supports_binding, PLAN)
from atlas_sources.registry import read_json

ROOT = Path(__file__).resolve().parents[1]


def uri(value):
    return {"type": "uri", "value": value}


def literal(value):
    return {"type": "literal", "value": value}


def result(variables, rows, rid="fixture"):
    return {"raw": json.dumps({"head": {"vars": variables}, "results": {"bindings": rows}}).encode(),
            "evidence": {"resource_id": rid}}


def public_asset(rid):
    resource = next(r for r in read_json(ROOT / "data/registry/resources.json") if r["id"] == rid)
    pin = read_json(ROOT / "data/resources.lock.json")[rid]
    return {"raw": (snapshot_dir(ROOT, resource, pin["sha256"]) / resource["filename"]).read_bytes(),
            "resource": resource, "evidence": {"resource_id": rid, "sha256": pin["sha256"]}}


class OfficialRdfTests(unittest.TestCase):
    def test_dotless_source_uri_is_distinct_from_display_notation(self):
        self.assertEqual(nace_code(NACE2 + "0111"), "01.11")
        self.assertEqual(nace_code(NACE2 + "310"), "31.0")
        with self.assertRaises(ValueError):
            nace_code(NACE2 + "31.00")

    def test_rdf_component_preserves_original_source_version_and_exact_term_location(self):
        a = public_asset("nace2-cellar-selected-notes-20261109")
        nodes = rdf_nodes(a)
        self.assertEqual(len(nodes), 22)
        n = next(n for n in nodes if n["code"] == "31.09")
        self.assertEqual(n["id"], "NACE:Rev.2:31.09@cellar-20261109")
        self.assertEqual(n["canonical_node_id"], "NACE:Rev.2:31.09")
        row = json.loads(a["raw"])["results"]["bindings"][n["field_result_rows"]["notes.includes_also"] - 1]
        self.assertEqual(row["o"]["value"], n["notes"]["includes_also"])
        self.assertIn("French polishing", n["notes"]["includes_also"])

    def test_reverse_no_source_row_keeps_blank_level_and_publisher_count_one(self):
        header = ["Level", "NACE_Rev_2_Code", "NACE_Rev_2_Title", "NACE_Rev_2_1_Code", "NACE_Rev_2_1_Title",
                  "Common_Content", "NumberOfCorresponding_NACE2", "TypeOfMapping", "TypeOfCorrespondence"]
        rows = [{"row": 1, "cells": dict(zip("ABCDEFGHI", header))},
                {"row": 2, "cells": dict(zip("ABCDEFGHI", ["", "", "", "46.89", "new", "no link", "1", "", ""]))}]
        with patch("atlas_sources.furniture_followup.read_workbook", return_value={"Sheet0": rows}):
            e = reverse_correspondence({"raw": b"fixture", "evidence": {}}, [{"code": "46.89", "level": 4}])[0]
        self.assertIsNone(e["from"])
        self.assertIsNone(e["level"])
        self.assertEqual(e["publisher_correspondence_count"], 1)
        self.assertEqual(e["publisher_count_check"], "not_applicable_no_source_endpoint")
        self.assertEqual(e["target_level"], 4)

    def direct_assets(self):
        association = NACE2 + "NACE2_ISIC4_409"
        rows = [{"association": uri(association), "p": uri(p), "o": uri(o)} for p, o in
                [(RDF_TYPE, XKOS + "ConceptAssociation"), (XKOS + "sourceConcept", NACE2 + "3109"),
                 (XKOS + "targetConcept", UN4 + "3100")]]
        pred = [{"s": uri(NACE2 + "3109"), "p": uri(SKOS + "closeMatch"), "o": uri(UN4 + "3100")}]
        return result(["association", "p", "o"], rows), result(["s", "p", "o"], pred)

    def test_direct_publisher_close_match_does_not_become_approved_exact_match(self):
        a, b = self.direct_assets()
        e = xkos_correspondence(a, b, [{"code": "3100"}])[0]
        self.assertEqual(e["publisher_relation"], "closeMatch")
        self.assertIsNone(e["relation"])
        self.assertIsNone(e["allocation_weight"])
        self.assertEqual(e["status"], "not_reviewed")

    def test_missing_or_competing_mapping_predicates_fail_instead_of_disappearing(self):
        a, b = self.direct_assets()
        with self.assertRaisesRegex(ValueError, "missing independently observed"):
            xkos_correspondence(a, result(["s", "p", "o"], []), [{"code": "3100"}])
        value = json.loads(b["raw"])
        value["results"]["bindings"].append({"s": uri(NACE2 + "3109"), "p": uri(SKOS + "exactMatch"), "o": uri(UN4 + "3100")})
        b["raw"] = json.dumps(value).encode()
        with self.assertRaisesRegex(ValueError, "competing"):
            xkos_correspondence(a, b, [{"code": "3100"}])

    def test_source_pair_disagreement_is_retained_without_mutation(self):
        euro = [{"from": "NACE:Rev.2:46.6", "to": "ISIC:Rev.4:466"}]
        unsd = [{"from": "ISIC:Rev.4:465", "to": "NACE:Rev.2:46.6"}]
        before = copy.deepcopy((euro, unsd))
        d = compare_publisher_pairs(euro, unsd)
        self.assertEqual(d["only_eurostat"][0][1], "ISIC:Rev.4:466")
        self.assertEqual(d["only_unsd"][0][1], "ISIC:Rev.4:465")
        self.assertEqual((euro, unsd), before)

    def test_complete_queries_are_bound_to_the_exact_url_and_query_bytes(self):
        a = public_asset("nace-cellar-current-positive-control-20261109")
        check_queries(ROOT, {"control": a})
        a["resource"] = {**a["resource"], "query_sha256": "changed"}
        with self.assertRaisesRegex(ValueError, "query text/URL/hash"):
            check_queries(ROOT, {"control": a})


class AuditAndReviewTests(unittest.TestCase):
    def audit_assets(self, control):
        return {
            "nace-cellar-correspondence-schemes-20261109": result(["g", "table", "scheme", "other"], []),
            "nace-cellar-current-mapping-targets-20261109": result(["p", "targetNamespace"], []),
            "nace-cellar-current-incoming-isic-20261109": result(["g", "s", "p", "o"], []),
            "nace-cellar-current-positive-control-20261109": result(["count"], [{"count": literal(str(control))}]),
            "nace-showvoc-catalog-20261109": {"raw": json.dumps({"result": [{"name": "NACE", "visibility": "PUBLIC"}]}).encode()}}

    def test_empty_query_without_matching_positive_control_cannot_prove_absence(self):
        with self.assertRaisesRegex(ValueError, "positive scheme control"):
            direct_audit(self.audit_assets(0), [{}] * 1047)
        r = direct_audit(self.audit_assets(1047), [{}] * 1047)
        self.assertEqual(r["status"], "not_observed_in_audited_cellar_snapshot")
        self.assertIn("not a publisher statement", r["limits"])

    def test_official_activity_allocation_requires_matching_endpoint_and_authority(self):
        b = {"node_id": "NACE:Rev.2:23.42", "claim_ids": ["allocation"], "basis": "explicit_official_crosswalk_activity_allocation"}
        c = {"document": "row", "field": "common_content", "role": "official_activity_allocation",
             "allocated_node_id": b["node_id"], "activity_key": "ceramic"}
        d = {"row": {"from": b["node_id"], "to": "NACE:Rev.2.1:31.00", "evidence": {"resource_id": "nace2-nace21-correspondence-20260831"}}}
        self.assertTrue(supports_binding(b, {"allocation": c}, d, {"key": "ceramic"}))
        d["row"]["evidence"]["resource_id"] = "a-product-table"
        with self.assertRaisesRegex(ValueError, "invalid publisher activity allocation"):
            supports_binding(b, {"allocation": c}, d, {"key": "ceramic"})

    def test_current_parts_cannot_silently_gain_a_legacy_approval(self):
        followup = read_json(ROOT / PLAN)
        a = copy.deepcopy(next(a for a in followup["activities"] if a["status"] == "reviewed_current_multisource_activity"))
        claims = {c["id"]: c for c in followup["claims"]}
        docs = {b["node_id"]: {"source_id": b["node_id"].split(":")[0]} for b in a["source_bindings"] + a["candidate_source_bindings"]}
        validate_slice(a, claims, docs)
        a["candidate_source_bindings"].pop()
        with self.assertRaisesRegex(ValueError, "both historical gaps"):
            validate_slice(a, claims, docs)

    def test_followup_keeps_original_pending_binding_and_issue_history(self):
        original = read_json(ROOT / "data/research/furniture-review.json")
        before = copy.deepcopy(original)
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            for p in ["data/research/furniture-review.json", PLAN]:
                target = root / p
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(ROOT / p, target)
            updated = extend_plan(root, original)
            self.assertEqual(original, before)
            previous_ids = {n["id"] for k in ("navigation", "anchors", "activities") for n in original[k]}
            current_ids = [n["id"] for k in ("navigation", "anchors", "activities") for n in updated[k]]
            self.assertTrue(previous_ids <= set(current_ids))
            self.assertEqual(len(current_ids), len(set(current_ids)))
            self.assertEqual(original["anchors"], updated["anchors"])
            ceramic = next(a for a in updated["activities"] if a["key"] == "ceramic")
            self.assertEqual(ceramic["binding_history"][0]["previous_binding"]["relation"], None)
            self.assertEqual(ceramic["source_bindings"][-1]["basis"], "explicit_official_crosswalk_activity_allocation")
            self.assertEqual(len(updated["claims"]), 68)
            self.assertTrue(all(i.get("history") for i in updated["issues"][:5]))
            (root / "data/research/furniture-review.json").write_text("changed")
            with self.assertRaisesRegex(ValueError, "parent furniture review changed"):
                extend_plan(root, original)


if __name__ == "__main__":
    unittest.main()
