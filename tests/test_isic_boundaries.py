import json
import tempfile
import unittest
from pathlib import Path
from atlas_sources.acquire import sha256
from atlas_sources.isic_boundaries import correspondence_rows, extend_plan
from atlas_sources.isic_priority import validate_activity, validate_mapping


class BoundaryEvidenceTests(unittest.TestCase):
    def activity(self):
        return {"key": "current-masks", "status": "accepted_current_activity", "parent_rev5_code": "3250",
                "source_bindings": [{"node_id": "ISIC:Rev.5:3250", "relation": "broadMatch", "claim_ids": ["new"]}]}

    def test_current_activity_is_admitted_without_inventing_old_binding(self):
        a = self.activity()
        validate_activity(a, {"new": {"document": "ISIC:Rev.5:3250", "role": "inclusion"}})
        a['source_bindings'].append({'node_id': 'ISIC:Rev.4:3250', 'relation': 'broadMatch', 'claim_ids': ['old']})
        with self.assertRaisesRegex(ValueError, 'edition claims'):
            validate_activity(a, {"new": {"document": "ISIC:Rev.5:3250", "role": "inclusion"},
                                  "old": {"document": "ISIC:Rev.4:3250", "role": "inclusion"}})

    def test_current_only_mask_does_not_validate_old_crosswalk(self):
        m = {'from_code': '1399', 'to_code': '3250', 'origin': 'atlas_research_supplement',
             'status': 'accepted_scoped_overlap', 'relation': 'relatedMatch', 'activity_ids': ['mask']}
        with self.assertRaisesRegex(ValueError, 'both endpoints'):
            validate_mapping(m, {'mask': self.activity()}, {})

    def test_product_inclusion_cannot_become_activity_equivalence(self):
        a = self.activity();a['source_bindings'][0]['node_id'] = 'CPC:2.1:48160'
        with self.assertRaisesRegex(ValueError, 'product evidence'):
            validate_activity(a, {})

    def test_pdf_table_uses_first_product_not_corresponding_old_product_column(self):
        text = ('HS 2007     ISIC 4\n'
                ' 32196 Sanitary articles 9619 27190*, 1709\n'
                ' 2719 27190 Other textile articles 6307 27190* 1392\n')
        links = correspondence_rows([{'pdf_page': 68, 'text': text, 'evidence': {'pdf_page': 68}}],
                                    {'1709', '1392'}, {'27190'})
        self.assertEqual([(x['product_code'],x['industry_code']) for x in links], [('27190','1392')])
        self.assertIsNone(links[0]['relation'])
        self.assertFalse(links[0]['semantic_equivalence'])

    def test_auxiliary_table_requires_header_and_known_industry(self):
        page = {'pdf_page':56,'text':'1740 17400 Ice 2201.90* 17400 3530\n','evidence':{}}
        with self.assertRaisesRegex(ValueError, 'coverage incomplete'):
            correspondence_rows([page], {'3530'}, {'17400'})
        page['text']='ISIC 4\n'+page['text']
        with self.assertRaisesRegex(ValueError, 'invalid auxiliary'):
            correspondence_rows([page], {'1050'}, {'17400'})

    def test_repeated_table_row_cannot_silently_overwrite_provenance(self):
        page={'pdf_page':56,'text':'ISIC 4\n1740 17400 Ice 2201.90* 17400 3530\n','evidence':{}}
        with self.assertRaisesRegex(ValueError,'duplicate'):
            correspondence_rows([page,page], {'3530'}, {'17400'})

    def test_followup_is_bound_to_the_prior_review_bytes(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);folder=root/'data/research';folder.mkdir(parents=True)
            (folder/'isic-priority-review.json').write_text('changed prior review')
            (folder/'isic-boundary-review.json').write_text(json.dumps({'parent_priority_sha256':'old'}))
            with self.assertRaisesRegex(ValueError,'parent review changed'):
                extend_plan(root,{})

    def test_followup_preserves_held_mapping_history_and_baseline(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);folder=root/'data/research';folder.mkdir(parents=True)
            raw=b'prior';(folder/'isic-priority-review.json').write_bytes(raw)
            original={'reviewed_input_sha256':{},'claims':[],'activities':[],
                      'mappings':[{'id':'pending','rationale':'prior reasoning','relation':None,'claim_ids':['old']}],
                      'atlas_identities':{},'new_issues':[]}
            delta={'parent_priority_sha256':sha256(raw),'reviewed_input_sha256':{},'claims':[],
                   'activities':[],'mappings':[],'atlas_identities':{},'activity_followups':[],
                   'mapping_followups':[{'mapping_id':'pending','rationale':'additional evidence','claim_ids':['new'],'status':'held'}],
                   'issue_followups':[],'directory_proposals':[]}
            (folder/'isic-boundary-review.json').write_text(json.dumps(delta))
            result=extend_plan(root,original)
            self.assertEqual(result['mappings'][0]['history'][0]['rationale'],'prior reasoning')
            self.assertIsNone(result['mappings'][0]['relation'])
            self.assertEqual(original['mappings'][0]['claim_ids'],['old'])


if __name__=='__main__':
    unittest.main()
