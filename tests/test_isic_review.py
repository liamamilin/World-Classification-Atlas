import json
import tempfile
import unittest
from pathlib import Path

from atlas_sources.isic_review import (audit_errata, check_relation, components, edge_fingerprint,
                                      erratum_fingerprint, inverse, review, text_agreement)


def node(code, edition):
    return {"code": code, "id": f"ISIC:{edition}:{code}", "parents": [] if code == 'A' else ['A'],
            "component": "fixture-notes", "label": "Fixture", "definition": "Scope " + code,
            "evidence": {"resource_id": edition, "sha256": edition, "row": code}}


def edge(a, b):
    return {"id": a + ">" + b, "from": "ISIC:Rev.4:" + a, "to": "ISIC:Rev.5:" + b,
            "from_code": a, "to_code": b, "original_fields": {"row": a + b},
            "evidence": {"resource_id": "map", "sha256": "map", "row": a + b},
            "publisher_uncertainty": False, "qualified_code_issues": [], "updated_notes_affected_codes": [],
            "historical_skos_candidate": "narrowMatch", "topology": "one_to_many",
            "decision_status": "review_real_change", "gsim_ids": ["RC4.1"]}


class ReviewTests(unittest.TestCase):
    def test_word_agreement_does_not_ignore_a_changed_allocation(self):
        self.assertEqual(text_agreement('a\r\nb', 'a\n b'), 'same_word_sequence')
        self.assertEqual(text_agreement('a 1812', 'a 1811'), 'different_word_sequence')
        self.assertEqual(text_agreement('a b', 'a b a b'), 'current_repeats_updated_twice')

    def test_disjoint_version_identity_even_for_reused_codes(self):
        a, b, c = edge('1103', '1104'), edge('1104', '1105'), edge('1103', '1103')
        groups = components([a, b, c])
        self.assertEqual(sorted(len(g) for g in groups), [1, 2])

    def test_inverse_mapping_direction_and_no_transitive_merge(self):
        self.assertEqual(inverse('narrowMatch'), 'broadMatch')
        self.assertEqual(inverse('broadMatch'), 'narrowMatch')
        self.assertEqual(inverse('relatedMatch'), 'relatedMatch')

    def test_parent_erratum_blocks_even_an_explicit_relation(self):
        e = edge('4311', '4340');e['updated_notes_affected_codes'] = ['F']
        with self.assertRaisesRegex(ValueError, 'ancestor/class'):
            check_relation(e, 'relatedMatch', {'F': {'effect': 'allocation_review_required'}})
        check_relation(e, 'relatedMatch', {'F': {'effect': 'no_additional_scope_effect'}})

    def test_source_question_is_not_resolved_by_manual_graph_approval(self):
        e = edge('8522', '8532');e['publisher_uncertainty'] = True
        with self.assertRaises(ValueError):
            check_relation(e, 'relatedMatch', {})

    def test_related_review_can_be_conservative_but_not_stronger(self):
        e = edge('2610', '2611')
        check_relation(e, 'relatedMatch', {})
        with self.assertRaises(ValueError):
            check_relation(e, 'exactMatch', {})

    def test_text_equality_cannot_release_allocation_without_a_decision(self):
        n = node('1105', 'Rev.5')
        note = {'code': '1105', 'original_note_2024': 'Old', 'updated_note_2026': n['definition'], 'evidence': {}}
        d = {'code': '1105', 'effect': 'allocation_review_required', 'reviewed_fingerprint': erratum_fingerprint(note, n)}
        result, _ = audit_errata([note], [node('A', 'Rev.5'), n], [d])
        self.assertEqual(result[0]['text_agreement'], 'same_word_sequence')
        self.assertEqual(result[0]['effect'], 'allocation_review_required')
        with self.assertRaises(ValueError):
            audit_errata([note], [n], [])

    def test_current_text_conflict_cannot_be_bypassed_by_editorial_label(self):
        n = node('5221', 'Rev.5')
        note = {'code': '5221', 'original_note_2024': 'site', 'updated_note_2026': 'main site', 'evidence': {}}
        n['definition'] = 'mine site'
        d = {'code': '5221', 'effect': 'no_additional_scope_effect', 'reviewed_fingerprint': erratum_fingerprint(note, n)}
        with self.assertRaisesRegex(ValueError, 'conflicting current text'):
            audit_errata([note], [n], [d])

    def fixture(self, root):
        old = [node('A', 'Rev.4'), node('2610', 'Rev.4')]
        new = [node('A', 'Rev.5'), node('2611', 'Rev.5'), node('2619', 'Rev.5')]
        edges = [edge('2610', '2611'), edge('2610', '2619')]
        choices = [{"from_code": e['from_code'], "to_code": e['to_code'], "relation": 'narrowMatch',
                    "rationale": 'Explicit reviewed fixture', "reviewed_fingerprint": edge_fingerprint(e, old[1], new[i+1])}
                   for i, e in enumerate(edges)]
        plan = {"reviewed_input_sha256": {'Rev.4': 'Rev.4', 'Rev.5': 'Rev.5', 'map': 'map'},
                "reviewer": 'Test', "reviewed_on": '2026-11-08', "scheme_id": 'Atlas-fixture',
                "errata_reviews": [], "cohorts": [{"id": 'split', "rationale": 'Scope split', "edges": choices}],
                "issues": [], "atlas_identities": {'A': 'Atlas-root', '2611': 'Atlas-cell', '2619': 'Atlas-other'}}
        path = root / 'data/research/isic-expanded-review.json';path.parent.mkdir(parents=True)
        path.write_text(json.dumps(plan))
        return old, new, edges, plan, path

    def test_reviewed_split_builds_separate_nodes_and_partial_reverse_lookup(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp);old, new, edges, _, _ = self.fixture(root)
            result = review(root, edges, old, new, [], {'cases': []}, [])
            self.assertEqual(result['statistics']['directory_kinds'], {'source_derived_navigation': 1, 'reviewed_activity': 2})
            public = json.loads((root/'data/atlas/economy/reviewed-directory-index.json').read_text())
            reverse = public['source_to_atlas']['ISIC:Rev.4:2610']
            self.assertEqual(len(reverse), 2)
            self.assertEqual({b['relation_atlas_to_source'] for b in reverse}, {'broadMatch'})
            self.assertFalse(any('definition' in n or 'label' in n for n in public['concepts']))
            self.assertEqual({n['parents'][0] for n in public['concepts'] if n['kind']=='reviewed_activity'}, {'Atlas-root'})

    def test_review_must_include_all_companion_split_edges(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);old,new,edges,plan,path=self.fixture(root)
            plan['cohorts'][0]['edges'].pop();path.write_text(json.dumps(plan))
            with self.assertRaisesRegex(ValueError, 'omitted/duplicated'):
                review(root,edges,old,new,[],{'cases':[]},[])

    def test_scope_change_invalidates_review_even_with_same_codes(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);old,new,edges,_,_=self.fixture(root)
            new[1]['definition'] = 'Changed allocation'
            with self.assertRaisesRegex(ValueError, 'scope or correspondence evidence changed'):
                review(root,edges,old,new,[],{'cases':[]},[])

    def test_identity_reuse_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);old,new,edges,plan,path=self.fixture(root)
            plan['atlas_identities']['2619']='Atlas-cell';path.write_text(json.dumps(plan))
            with self.assertRaisesRegex(ValueError, 'identity registry'):
                review(root,edges,old,new,[],{'cases':[]},[])


if __name__ == '__main__':
    unittest.main()
