import copy
import unittest
from pathlib import Path

from atlas_sources.acquire import snapshot_dir
from atlas_sources.furniture import PUBLIC, checked_qa, topology
from atlas_sources import furniture_naf as naf
from atlas_sources.registry import read_json

ROOT = Path(__file__).resolve().parents[1]


class InseeSourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        resources = {r["id"]: r for r in read_json(ROOT / "data/registry/resources.json")}
        lock = read_json(ROOT / "data/resources.lock.json")
        cls.assets = {}
        for rid in (naf.OLD_STRUCTURE, naf.STRUCTURE, naf.FORWARD, naf.REVERSE):
            r = resources[rid]
            digest = lock[rid]["sha256"]
            raw = (snapshot_dir(ROOT, r, digest) / r["filename"]).read_bytes()
            cls.assets[rid] = {"raw": raw, "resource": r, "evidence": {"resource_id": rid, "sha256": digest}}
        cls.old = naf.old_structure(cls.assets[naf.OLD_STRUCTURE])
        cls.current = naf.current_structure(cls.assets[naf.STRUCTURE])
        cls.forward = naf.correspondence(cls.assets[naf.FORWARD], cls.old, cls.current, topology)
        cls.reverse = naf.correspondence(cls.assets[naf.REVERSE], cls.current, cls.old, topology)

    def test_published_hierarchies_keep_both_subclass_parents(self):
        self.assertEqual(checked_qa(self.old)["levels"], {1: 21, 2: 88, 3: 272, 4: 615, 5: 732})
        self.assertEqual(checked_qa(self.current)["levels"], {1: 22, 2: 87, 3: 287, 4: 651, 5: 747})
        old = next(n for n in self.old if n["code"] == "31.01Z")
        new = next(n for n in self.current if n["code"] == "31.00G")
        self.assertEqual(old["parents"], ["31.01"])
        self.assertEqual(new["parents"], ["31.00"])
        broken = {**self.assets[naf.OLD_STRUCTURE], "raw": self.assets[naf.OLD_STRUCTURE]["raw"][:-8]}
        with self.assertRaisesRegex(ValueError, "record bounds"):
            naf.old_structure(broken)

    def test_official_rows_keep_direction_specific_scope_and_null_endpoint(self):
        audit = naf.audit_correspondence(self.forward, self.reverse)
        self.assertEqual((audit["forward_rows"], audit["reverse_rows"]), (1242, 1242))
        self.assertTrue(audit["reversed_pair_sets_equal"])
        fwd = next(e for e in self.forward if (e["from_code"], e["to_code"]) == ("23.42Z", "23.42Y"))
        rev = next(e for e in self.reverse if (e["from_code"], e["to_code"]) == ("23.42Y", "23.42Z"))
        self.assertEqual((fwd["publisher_mapping_type"], rev["publisher_mapping_type"]), ("Multiple", "Unique"))
        self.assertIsNone(fwd["relation"])
        self.assertIsNone(rev["relation"])
        unallocated, = (e for e in self.reverse if e["to"] is None)
        self.assertEqual(unallocated["from_code"], "46.89Y")
        self.assertIsNone(unallocated["publisher_mapping_type"])

    def test_unlisted_operation_is_an_observation_on_existing_rows(self):
        review = read_json(ROOT / naf.PLAN)
        official = {e["id"]: e for e in self.forward + self.reverse}
        observation = next(s for s in review["text_observations"] if s["id"] == "naf-old-shop-component-text")
        checked, = naf.check_text_observations([observation], official)
        self.assertEqual([r["mentioned"] for r in checked["directional_observations"]], [False, False])
        changed = copy.deepcopy(official)
        changed[observation["mapping_ids"][0]]["common_content"] = "composants intégrés"
        with self.assertRaisesRegex(ValueError, "common-content observation changed"):
            naf.check_text_observations([observation], changed)

    def test_pending_independent_parts_and_specialist_finishing_are_separate(self):
        directory = read_json(ROOT / PUBLIC)
        activities = {n.get("key"): n for n in directory["concepts"] if n.get("key")}
        parts = activities["wooden-built-in-components-for-shop-furniture"]
        self.assertIn("FR_NAF:2025:31.00G", {b["node_id"] for b in parts["source_bindings"]})
        self.assertEqual({b["node_id"] for b in parts["candidate_source_bindings"]},
                         {"ISIC:Rev.4:3100", "FR_NAF:Rev.2:31.01Z"})
        factory = activities["manufacture-finished-wooden-shop-counters-with-built-ins"]
        self.assertNotIn(parts["id"], factory["parents"])
        self.assertIn("ISIC:Rev.4:3100", {b["node_id"] for b in factory["source_bindings"]})
        special = activities["contract-finishing-office-and-shop-furniture"]
        other = activities["contract-finishing-other-furniture-for-professionals"]
        self.assertNotIn("NACE:Rev.2:31.01", {b["node_id"] for b in special["source_bindings"]})
        self.assertIn("NACE:Rev.2:31.09", {b["node_id"] for b in other["source_bindings"]})
        sanitary = activities["ceramic-sanitary-fixtures"]
        self.assertEqual({b["node_id"] for b in sanitary["source_bindings"] if b["node_id"].startswith("FR_NAF:")},
                         {"FR_NAF:Rev.2:23.42Z", "FR_NAF:2025:23.42Y"})
        self.assertEqual(len(directory["official_pair_comparisons"]), 3)
