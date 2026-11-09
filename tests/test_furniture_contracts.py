import copy
import json
import tempfile
import unittest
from pathlib import Path

from atlas_sources.acquire import sha256
from atlas_sources.furniture import PUBLIC, validate_slice
from atlas_sources import furniture_contracts as contracts
from atlas_sources.registry import read_json

ROOT = Path(__file__).resolve().parents[1]


class ContractorAndPartsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.directory = read_json(ROOT / PUBLIC)
        cls.claims = {c["id"]: c for c in cls.directory["claims"]}

    def activity(self, key):
        return copy.deepcopy(next(a for a in self.directory["concepts"] if a.get("key") == key))

    def test_contractor_rule_and_identified_input_are_required(self):
        for key in contracts.CONTRACT_INPUTS:
            with self.subTest(activity=key):
                a = self.activity(key)
                contracts.check_contractor_scope(a, self.claims)
                bad = copy.deepcopy(a)
                bad["contractor_scope"]["activity_role"] = "principal"
                with self.assertRaisesRegex(ValueError, "specific input and contractor conditions"):
                    contracts.check_contractor_scope(bad, self.claims)
                bad = copy.deepcopy(a)
                bad["contractor_scope"]["rule_claims"]["ISIC:Rev.5"] = "FM009"
                with self.assertRaisesRegex(ValueError, "each edition's contractor rule"):
                    contracts.check_contractor_scope(bad, self.claims)
                del a["contractor_scope"]
                with self.assertRaisesRegex(ValueError, "specific input and contractor conditions"):
                    contracts.check_contractor_scope(a, self.claims)

    def test_historical_parts_require_nonpartial_nace_side_and_single_isic_target(self):
        a = self.activity(contracts.PARTS_KEY)
        docs = {b["node_id"]: {"source_id": b["node_id"].split(":")[0]} for b in a["source_bindings"]}
        review = read_json(ROOT / contracts.PLAN)
        parts_claims = [self.claims[c] for b in a["source_bindings"] for c in b["claim_ids"]]
        for c in parts_claims:
            if c["role"] == "national_parts_index":
                docs[c["document"]] = {"code": "31090", "description": contracts.INDEX_TERMS[1]}
        flag, = (c for c in review["claims"] if c["field"] == "publisher_partial_flags.NACE2part")
        edge = {"from": "ISIC:Rev.4:3100", "to": "NACE:Rev.2:31.09",
                "publisher_partial_flags": {"ISIC4part": "1", "NACE2part": "0"}, "to_degree": 1,
                "evidence": {"resource_id": "isic4-nace2-correspondence"}}
        docs[flag["document"]] = edge
        validate_slice(a, self.claims, docs)
        for change in ({"to_degree": 2}, {"publisher_partial_flags": {"ISIC4part": "0", "NACE2part": "1"}}):
            docs[flag["document"]] = {**edge, **change}
            with self.assertRaisesRegex(ValueError, "directional allocation"):
                validate_slice(a, self.claims, docs)
        shop = self.activity("wooden-built-in-components-for-shop-furniture")
        self.assertEqual(shop["candidate_source_bindings"][0]["node_id"], "ISIC:Rev.4:3100")
        self.assertIsNone(shop["candidate_source_bindings"][0]["relation"])

    def test_contractor_conflict_is_unresolved_in_the_official_row_and_candidate(self):
        a = self.activity("contract-finishing-recognisable-new-household-furniture")
        self.assertIn("NACE:Rev.2:31.09", {b["node_id"] for b in a["source_bindings"]})
        self.assertEqual([(b["node_id"], b["relation"]) for b in a["candidate_source_bindings"]],
                         [("NACE:Rev.2:31.01", None)])
        row = next(r for r in self.directory["official_reviews"]
                   if r["evidence"]["resource_id"] == "nace21-nace2-correspondence" and r["evidence"]["row"] == 555)
        decision = next(r for r in row["review"]["scope_followups"] if a["id"] in r["activity_ids"])
        self.assertEqual(decision["status"], "held_for_this_activity")
        self.assertIsNone(decision["relation"])


class PublicationRecheckTests(unittest.TestCase):
    def test_changed_table_cannot_be_counted_as_an_unchanged_refresh(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            info = {"acquisition_path": "data/acquisition/20261109T003503106764Z-a46eea10.json"}
            path = root / info["acquisition_path"]
            path.parent.mkdir(parents=True)
            asset = {"evidence": {"sha256": "pinned", "url": "https://example.org/table"}}
            rid = contracts.RECHECKED[0]
            row = {"resource_id": rid, "http_status": 200, "status": "drift",
                   "sha256": "changed", "url": asset["evidence"]["url"]}
            path.write_text(json.dumps([row]), encoding="utf-8")
            info["acquisition_sha256"] = sha256(path.read_bytes())
            with self.assertRaisesRegex(ValueError, "refresh does not match"):
                contracts.publication_audit(root, {"release_recheck": info}, {rid: asset})

    def test_only_registry_title_table_and_active_links_are_read(self):
        html = b"""<table><tr><td>Outside registry</td></tr></table>
        <!-- <a href="/archived.xlsx">commented</a> -->
        <a href="/active.xlsx">active</a>
        <table id="example">
        <tr><td><a href="/detail/123">123</a></td><td>Correction</td>
        <td>Sanitary fixtures</td><td>9 Nov 2026</td></tr>
        </table>"""
        page = contracts.PublicationPage(html, "https://example.org/registry")
        self.assertEqual(page.rows, [(5, ["123", "Correction", "Sanitary fixtures", "9 Nov 2026"])])
        self.assertEqual(page.links[0]["url"], "https://example.org/active.xlsx")
        self.assertEqual(len(page.links), 2)
