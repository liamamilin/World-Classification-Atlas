import copy
import unittest
from pathlib import Path

from atlas_sources.furniture import PUBLIC, validate_slice
from atlas_sources.furniture_materials import BASIS, PLAN, check_comparisons
from atlas_sources.registry import read_json

ROOT = Path(__file__).resolve().parents[1]


class MaterialBoundaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.directory = read_json(ROOT / PUBLIC)
        cls.activities = {a["id"]: a for a in cls.directory["concepts"]}
        cls.claims = {c["id"]: c for c in cls.directory["claims"]}

    def activity(self, key):
        return copy.deepcopy(next(a for a in self.activities.values() if a.get("key") == key))

    def documents(self, activity):
        docs = {b["node_id"]: {"source_id": b["node_id"].split(":")[0], "parents": ["310"]}
                for b in activity["source_bindings"] + activity.get("candidate_source_bindings", [])}
        for c in self.claims.values():
            if c["role"] == "inclusion" and "@" in c["document"]:
                docs[c["document"]] = {"canonical_node_id": c["document"].split("@")[0]}
        return docs

    def test_material_child_requires_both_group_process_and_correct_class_scope(self):
        for material, code in (("wooden", "3101"), ("all-metal", "3102")):
            with self.subTest(material=material):
                a = self.activity(f"new-{material}-furniture-surface-finishing")
                docs = self.documents(a)
                validate_slice(a, self.claims, docs, self.activities)
                b = next(b for b in a["source_bindings"] if b.get("basis") == BASIS)
                process, scope = b["claim_ids"]
                for single in (process, scope):
                    b["claim_ids"] = [single]
                    with self.assertRaisesRegex(ValueError, "bounded group process and class scope"):
                        validate_slice(a, self.claims, docs, self.activities)
                b["claim_ids"] = [process, scope]
                docs["ISIC:Rev.5:" + code]["parents"] = ["999"]
                with self.assertRaisesRegex(ValueError, "bounded group process and class scope"):
                    validate_slice(a, self.claims, docs, self.activities)

    def test_cpc_product_reference_cannot_approve_an_isic_activity_binding(self):
        a = self.activity("wooden-built-in-components-for-shop-furniture")
        docs = self.documents(a)
        official = next(c for c in self.claims.values() if c.get("activity_key") == a["key"])
        docs[official["document"]] = {"from": "NACE:Rev.2.1:31.00", "to": "NACE:Rev.2:31.01",
                                      "evidence": {"resource_id": "nace21-nace2-correspondence"}}
        validate_slice(a, self.claims, docs)
        candidate = next(b for b in a["candidate_source_bindings"] if b["node_id"] == "ISIC:Rev.4:3100")
        a["candidate_source_bindings"].remove(candidate)
        product, = (c for c in candidate["claim_ids"] if self.claims[c]["role"] == "auxiliary_product_link")
        docs[self.claims[product]["document"]] = {"source_id": "UN_CPC"}
        a["source_bindings"].append({**candidate, "relation": "broadMatch", "claim_ids": [product]})
        with self.assertRaisesRegex(ValueError, "lacks direct source inclusion"):
            validate_slice(a, self.claims, docs)

    def test_missing_pair_requires_verified_table_adjacency(self):
        comparison = read_json(ROOT / PLAN)["comparisons"][0]
        record = self.directory["official_pair_comparisons"][0]
        edges = record["adjacent_rows"]
        rid = comparison["resource_id"]
        mappings = {m["id"]: m for m in self.directory["research_mappings"]}
        assets = {rid: {"evidence": record["evidence"]}}
        result, = check_comparisons([comparison], edges, assets, mappings, self.claims)
        self.assertIsNone(result["official_mapping_id"])
        self.assertEqual(result["status"], "absent_in_checked_table")
        with self.assertRaisesRegex(ValueError, "official adjacency changed"):
            check_comparisons([comparison], edges[:1], assets, mappings, self.claims)
        new_row = {**edges[0], "from": comparison["absent_from"], "to": comparison["absent_to"]}
        with self.assertRaisesRegex(ValueError, "expected absent official pair now present"):
            check_comparisons([comparison], edges + [new_row], assets, mappings, self.claims)

    def test_conflict_and_bounded_positive_control_keep_separate_ids_and_scopes(self):
        sanitary = self.activity("ceramic-sanitary-fixtures")
        tiles = self.activity("non-refractory-ceramic-tiles-and-mosaics")
        self.assertEqual({b["node_id"] for b in sanitary["source_bindings"] if b["node_id"].startswith(("ISIC:", "NACE:"))},
                         {"ISIC:Rev.4:2392", "ISIC:Rev.5:2393", "NACE:Rev.2:23.42", "NACE:Rev.2.1:23.42"})
        same_code = next(r for r in self.directory["official_reviews"]
                         if (r["from"], r["to"]) == ("ISIC:Rev.4:2392", "ISIC:Rev.5:2392"))
        self.assertEqual(same_code["review"]["activity_ids"], [tiles["id"]])
        self.assertEqual(same_code["gsim_ids"], [])
        prior = next(r for r in self.directory["official_reviews"]
                     if (r["from"], r["to"]) == ("ISIC:Rev.4:2393", "ISIC:Rev.5:2393"))
        self.assertEqual(prior["review"]["relation"], "relatedMatch")
        followup, = prior["review"]["scope_followups"]
        self.assertEqual(followup["activity_ids"], [sanitary["id"]])
        self.assertIsNone(followup["relation"])
