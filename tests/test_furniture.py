import copy
import unittest
from pathlib import Path
from unittest.mock import patch

from atlas_sources.acquire import sha256
from atlas_sources.furniture import (parent_code, nace_nodes, nace_correspondence,
    isic_nace_correspondence, validate_slice, validate_research_mapping)
from atlas_sources.isic_priority import resolve_claim
from atlas_sources.registry import read_json

ROOT = Path(__file__).resolve().parents[1]


class NaceSourceTests(unittest.TestCase):
    def test_codes_preserve_dot_zero_and_derive_real_depth(self):
        self.assertEqual(parent_code('01.00', 'A'), '01.0')
        self.assertEqual(parent_code('31.00', 'C'), '31.0')
        with self.assertRaisesRegex(ValueError, 'invalid NACE'):
            parent_code('3100', 'C')

    def test_real_notes_have_complete_hierarchy_and_original_publisher_ids(self):
        resources = read_json(ROOT / 'data/registry/resources.json')
        r = next(r for r in resources if r['id'] == 'nace21-notes-20260930')
        p = next((ROOT / 'data/raw/NACE').rglob(r['filename']))
        nodes = nace_nodes({'raw': p.read_bytes(), 'evidence': {'resource_id':r['id'], 'sha256': sha256(p.read_bytes())}})
        self.assertEqual(len(nodes), 1047)
        leaf = next(n for n in nodes if n['code'] == '31.00')
        self.assertEqual(leaf['parents'], ['31.0'])
        self.assertEqual(leaf['publisher_id'], '4040')
        self.assertIn('stone, concrete and ceramic furniture', leaf['notes']['includes_also'])
        self.assertEqual(leaf['evidence']['row'], 409)

    def test_publisher_no_correspondence_row_survives_without_fake_endpoint(self):
        header = ['NACE21_Code','LEVEL','NACE21_Heading','NACE2_Code','NACE2_Heading',
                  'Common_Content','NumberOfCorresponding_NACE2','TypeOfMapping','TypeOfCorrespondence']
        rows = [{'row':1,'cells':dict(zip('ABCDEFGHI',header))},
                {'row':810,'cells':dict(zip('ABCDEFGHI',['46.89','4','new','','','conceptual note','0','','1:0']))}]
        with patch('atlas_sources.furniture.read_workbook', return_value={'Sheet0':rows}):
            edge = nace_correspondence({'raw':b'x','evidence':{}},[{'code':'46.89','level':4}])[0]
        self.assertIsNone(edge['to'])
        self.assertIsNone(edge['relation'])
        self.assertEqual(edge['topology'],'no_correspondence')
        self.assertEqual(edge['original_fields']['row'],810)

    def test_isic_partial_flags_are_not_weights_or_equivalence(self):
        raw = b'"ISIC4code","ISIC4part","NACE2code","NACE2part"\r\n"3100",1,"31.01",0\r\n"3100",1,"31.02",0\r\n'
        edges = isic_nace_correspondence({'raw':raw,'evidence':{}},[{'code':'3100'}])
        self.assertEqual(edges[0]['publisher_partial_flags'],{'ISIC4part':'1','NACE2part':'0'})
        self.assertEqual(edges[0]['topology'],'one_to_many')
        self.assertIsNone(edges[0]['relation'])
        self.assertIsNone(edges[0]['allocation_weight'])
        bad = raw.replace(b',1,', b',2,')
        with self.assertRaisesRegex(ValueError,'partial flag'):
            isic_nace_correspondence({'raw':bad,'evidence':{}},[{'code':'3100'}])


class FurnitureResearchTests(unittest.TestCase):
    def setUp(self):
        self.plan = read_json(ROOT / 'data/research/furniture-review.json')
        self.claims = {c['id']: c for c in self.plan['claims']}
        self.docs = {b['node_id']:{'source_id':b['node_id'].split(':')[0]} for a in self.plan['activities']
                     for b in a['source_bindings'] + a.get('candidate_source_bindings',[])}

    def test_all_seven_slices_have_same_object_multi_edition_evidence(self):
        for a in self.plan['activities']:
            validate_slice(a,self.claims,self.docs)
        self.assertEqual(len(self.plan['activities']),7)

    def test_slice_cannot_be_promoted_to_entire_class(self):
        a = copy.deepcopy(self.plan['activities'][0])
        a['source_bindings'][0]['relation']='exactMatch'
        with self.assertRaisesRegex(ValueError,'broader source class'):
            validate_slice(a,self.claims,self.docs)

    def test_missing_old_edition_and_pending_ceramic_cannot_be_hidden(self):
        a = copy.deepcopy(self.plan['activities'][0])
        a['source_bindings'] = a['source_bindings'][1:]
        with self.assertRaisesRegex(ValueError,'both ISIC'):
            validate_slice(a,self.claims,self.docs)
        a = copy.deepcopy(self.plan['activities'][0])
        a['candidate_source_bindings'][0]['relation']='broadMatch'
        with self.assertRaisesRegex(ValueError,'pending binding'):
            validate_slice(a,self.claims,self.docs)

    def test_crosswalk_chains_cannot_replace_shared_activity_or_official_authority(self):
        acts = {a['id']:a for a in self.plan['activities']}
        m = copy.deepcopy(self.plan['research_mappings'][0])
        validate_research_mapping(m,acts)
        m['official_mapping_id']='inferred-from-two-tables'
        with self.assertRaisesRegex(ValueError,'masquerade'):
            validate_research_mapping(m,acts)
        m['official_mapping_id']=None;m['from']='ISIC:Rev.5:9999'
        with self.assertRaisesRegex(ValueError,'both endpoints'):
            validate_research_mapping(m,acts)

    def test_clause_changed_bytes_invalidate_evidence(self):
        c={'id':'x','document':'NACE:Rev.2.1:31.00','field':'notes.includes','start':0,'end':3,
           'field_sha256':sha256(b'old'),'text_sha256':sha256(b'old'),'role':'inclusion'}
        with self.assertRaisesRegex(ValueError,'clause changed'):
            resolve_claim(c,{'NACE:Rev.2.1:31.00':{'notes':{'includes':'new'},'evidence':{}}})

    def test_reused_identity_and_every_leaf_and_incoming_row_are_visible(self):
        base = read_json(ROOT / 'data/research/isic-expanded-review.json')['atlas_identities']
        for n in self.plan['anchors']:
            self.assertEqual(n['id'],base[n['base_rev5_code']])
        rows = self.plan['official_reviews']
        self.assertEqual(len(rows),14)
        index=read_json(ROOT / 'data/atlas/economy/furniture-directory.json')
        self.assertIn('NACE:Rev.2:23.42',index['source_to_candidates'])
        self.assertNotIn('NACE:Rev.2:23.42',index['source_to_atlas'])
        for code in ('31.01','31.02','31.03','31.09'):
            self.assertIn('NACE:Rev.2:'+code,index['source_to_atlas'])


if __name__ == '__main__':
    unittest.main()
