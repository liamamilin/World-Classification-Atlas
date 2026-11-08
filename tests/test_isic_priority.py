import unittest
from atlas_sources.acquire import sha256
from atlas_sources.isic_priority import resolve_claim, validate_activity, validate_mapping


class PriorityEvidenceTests(unittest.TestCase):
    def claim(self):
        text = '范围\n- manufacturing of edible ice, see 1050\n'
        doc = {'notes': {'excludes': text}, 'evidence': {'resource_id': 'fixture', 'sha256': 'pinned'}}
        start, end = 3, len(text) - 1
        claim = {'id': 'evidence-ice', 'document': 'ISIC:Rev.5:3530', 'field': 'notes.excludes',
                 'start': start, 'end': end, 'field_sha256': sha256(text.encode()),
                 'text_sha256': sha256(text[start:end].encode()), 'role': 'exclusion_to_target',
                 'target_node_id': 'ISIC:Rev.5:1050'}
        return claim, {claim['document']: doc}

    def activity(self):
        return {'key': 'plant-milk', 'status': 'accepted_bounded_activity', 'parent_rev5_code': '1105',
                'source_bindings': [{'node_id': 'ISIC:Rev.4:1079', 'relation': 'broadMatch', 'claim_ids': ['old']},
                                    {'node_id': 'ISIC:Rev.5:1105', 'relation': 'broadMatch', 'claim_ids': ['new']}]}

    def mapping(self):
        return {'from_code': '1079', 'to_code': '1105', 'origin': 'atlas_research_supplement',
                'status': 'accepted_scoped_overlap', 'relation': 'relatedMatch', 'activity_ids': ['milk']}

    def test_unicode_span_and_original_field_are_recoverable(self):
        claim, docs = self.claim()
        public, selected = resolve_claim(claim, docs)
        self.assertEqual(selected, '- manufacturing of edible ice, see 1050')
        self.assertEqual(public['offset_unit'], 'unicode_codepoints_in_parsed_original_field')
        self.assertNotIn('selected_source_text', public)

    def test_changed_evidence_invalidates_even_unchanged_endpoint_codes(self):
        claim, docs = self.claim()
        docs[claim['document']]['notes']['excludes'] = 'changed allocation'
        with self.assertRaises(ValueError):
            resolve_claim(claim, docs)

    def test_exclusion_does_not_prove_activity_in_that_same_class(self):
        claim, docs = self.claim();public, _ = resolve_claim(claim, docs)
        activity = self.activity();activity['source_bindings'] = [
            {'node_id': 'ISIC:Rev.5:3530', 'relation': 'broadMatch', 'claim_ids': [public['id']]}]
        with self.assertRaisesRegex(ValueError, 'lacks source inclusion'):
            validate_activity(activity, {public['id']: public})

    def test_cross_reference_must_name_actual_target(self):
        claim, docs = self.claim();claim['target_node_id'] = 'ISIC:Rev.5:3530'
        with self.assertRaisesRegex(ValueError, 'does not name'):
            resolve_claim(claim, docs)

    def test_revision_reason_cannot_masquerade_as_source_inclusion(self):
        claim, docs = self.claim();claim['role'] = 'inclusion'
        with self.assertRaisesRegex(ValueError, 'cannot masquerade'):
            resolve_claim(claim, docs)

    def test_slice_is_not_equivalent_to_entire_parent_class(self):
        activity = self.activity();activity['source_bindings'][0]['relation'] = 'exactMatch'
        with self.assertRaisesRegex(ValueError, 'whole source-class'):
            validate_activity(activity, {})

    def test_supplement_never_fabricates_official_table_row(self):
        mapping = self.mapping();mapping['origin'] = 'official_row_review'
        with self.assertRaisesRegex(ValueError, 'masquerade'):
            validate_mapping(mapping, {'milk': self.activity()}, {})

    def test_scoped_association_cannot_upgrade_to_whole_class_containment(self):
        for relation in ['exactMatch', 'narrowMatch', 'broadMatch']:
            mapping = self.mapping();mapping['relation'] = relation
            with self.assertRaisesRegex(ValueError, 'whole-class containment'):
                validate_mapping(mapping, {'milk': self.activity()}, {})

    def test_accepted_supplement_requires_shared_activity_at_both_endpoints(self):
        mapping = self.mapping()
        validate_mapping(mapping, {'milk': self.activity()}, {})
        activity = self.activity();activity['source_bindings'][0]['node_id'] = 'ISIC:Rev.4:1050'
        with self.assertRaisesRegex(ValueError, 'both endpoints'):
            validate_mapping(mapping, {'milk': activity}, {})

    def test_uncertain_ice_candidate_has_no_approved_relation(self):
        mapping = self.mapping();mapping.update(status='held_after_research', relation='relatedMatch')
        with self.assertRaisesRegex(ValueError, 'held mapping'):
            validate_mapping(mapping, {}, {})
        mapping['relation'] = None
        validate_mapping(mapping, {}, {})

    def test_activity_evidence_cannot_silently_remove_publisher_question(self):
        mapping = self.mapping();mapping['origin'] = 'official_row_review'
        official = {('1079', '1105'): {'publisher_uncertainty': True, 'qualified_code_issues': []}}
        with self.assertRaisesRegex(ValueError, 'publisher question'):
            validate_mapping(mapping, {'milk': self.activity()}, official)


if __name__ == '__main__':
    unittest.main()
