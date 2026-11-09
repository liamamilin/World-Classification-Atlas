import unittest

from atlas_sources.hs_reference import resolve


def parse(notation, codes, cpc_id="CPC:3.0:00000"):
    nodes = [{"code": code, "id": f"HS:2022:{code}",
              "level": "subheading" if "." in code else "heading"} for code in codes]
    return resolve([{"cpc_id": cpc_id, "hs_notation": notation}], nodes)[0]


class HSReferenceTests(unittest.TestCase):
    def test_ranges_use_only_real_subheadings_under_the_same_heading(self):
        result = parse("3002.41-49, 3002.51/59", [
            "3002", "3002.40", "3002.41", "3002.42", "3002.49", "3002.51",
            "3002.55", "3002.59", "3003.42",
        ])
        self.assertEqual(result["target_ids"], [
            "HS:2022:3002.41", "HS:2022:3002.42", "HS:2022:3002.49", "HS:2022:3002.51", "HS:2022:3002.59",
        ])

    def test_missing_code_retains_valid_sibling(self):
        result = parse("0307.53 and 0307.59", ["0307.52", "0307.59"])
        self.assertEqual(result["target_ids"], ["HS:2022:0307.59"])
        self.assertEqual(result["resolution_status"], "pending")
        self.assertEqual(result["terms"][0]["attempted_codes"], ["0307.53"])

    def test_heading_reference_and_subheading_context_are_separate(self):
        result = parse("48.18, 4804.11 & .19; 8501.20, .40", [
            "4818", "4818.10", "4804.11", "4804.19", "8501.20", "8501.40",
        ])
        self.assertEqual(result["target_ids"], [
            "HS:2022:4818", "HS:2022:4804.11", "HS:2022:4804.19", "HS:2022:8501.20", "HS:2022:8501.40",
        ])

    def test_editorial_bare_suffix_is_limited_to_reviewed_clause(self):
        codes = ["9405.11", "9405.21", "9405.31", "9405.41"]
        checked = parse("9405.11, .21, 31, 41", codes, "CPC:3.0:46533")
        self.assertEqual(checked["target_ids"], ["HS:2022:" + code for code in codes])
        unrelated = parse("9405.11, .21, 31, 41", codes)
        self.assertEqual(unrelated["target_ids"], ["HS:2022:9405.11", "HS:2022:9405.21"])
        self.assertEqual(unrelated["resolution_status"], "pending")
