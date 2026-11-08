import io
import json
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch
from atlas_sources.isic import change_ids, code_without_section, derive_relation, parse_correspondence, parse_errata, validate_enrichment, curate
from atlas_sources.xlsx import read_workbook, unescape
from atlas_sources.acquire import check_payload


def node(code, edition):
    return {"id": f"ISIC:{edition}:{code}", "code": code, "label": "Fixture", "definition": None,
            "parents": [] if code == 'A' else ['A']}


def correspondence_row(index, first, second, gsim='', qualified=None):
    return {"row": index, "cells": {"A": qualified or 'A'+first, "B": first, "C": 'Old',
                                    "D": 'A'+second, "E": second, "F": 'New', "G": gsim, "H": ''}}


class OOXMLTests(unittest.TestCase):
    def test_xml_escape_is_decoded_once(self):
        self.assertEqual(unescape('a_x000D_b'), 'a\rb')
        self.assertEqual(unescape('_x005F_x000D_'), '_x000D_')

    def test_sparse_cells_and_original_row_numbers_survive(self):
        f = io.BytesIO()
        with zipfile.ZipFile(f, 'w') as z:
            z.writestr('xl/workbook.xml', '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets><sheet name="Test" sheetId="1" r:id="rId7"/></sheets></workbook>')
            z.writestr('xl/_rels/workbook.xml.rels', '<Relationships><Relationship Id="rId7" Target="worksheets/sheet3.xml"/></Relationships>')
            z.writestr('xl/worksheets/sheet3.xml', '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData><row r="9"><c r="A9" t="inlineStr"><is><t>0130</t></is></c><c r="G9" t="inlineStr"><is><t>Split off?</t></is></c></row></sheetData></worksheet>')
        rows = read_workbook(f.getvalue())['Test']
        self.assertEqual(rows[0]['row'], 9)
        self.assertEqual(rows[0]['cells'], {'A': '0130', 'G': 'Split off?'})

    def test_pdf_error_page_is_not_a_pdf(self):
        with self.assertRaises(ValueError):
            check_payload(b'not a PDF', {'format': 'pdf'})


class ISICSemanticTests(unittest.TestCase):
    def test_compound_gsim_typos_and_question_mark_are_not_discarded(self):
        self.assertEqual(change_ids('VC1- Code change; RC4.1 -  Breadown; RC4.2 - Split off?'), ['VC1','RC4.1','RC4.2'])
        with self.assertRaises(ValueError):
            change_ids('Unknown - invented change')

    def test_directional_whole_and_partial_relations(self):
        self.assertEqual(derive_relation(2,1,['RC4.1']), 'narrowMatch')
        self.assertEqual(derive_relation(1,2,['RC3.1']), 'broadMatch')
        self.assertEqual(derive_relation(2,2,['RC5']), 'relatedMatch')
        self.assertIsNone(derive_relation(1,1,['RC5']))
        self.assertIsNone(derive_relation(1,1,[],uncertain=True))

    def test_virtual_change_can_support_scope_equivalence(self):
        self.assertEqual(derive_relation(1,1,['VC1','VC2']), 'exactMatch')

    def test_no_change_row_with_incoming_transfer_is_not_exact(self):
        book={'ISIC4-5':[{'row':1,'cells':{'G':'Type of change in GSIM (blank means no change)'}},
                         correspondence_row(2,'0111','0111'), correspondence_row(3,'0112','0111','RC5 - Transfer')]}
        asset={'raw':b'fixture','evidence':{'resource_id':'fixture','sha256':'abc'}}
        with patch('atlas_sources.isic.read_workbook',return_value=book):
            edges,_=parse_correspondence(asset,[node('A','Rev.4'),node('0111','Rev.4'),node('0112','Rev.4')],
                                         [node('A','Rev.5'),node('0111','Rev.5')],[])
        self.assertEqual(edges[0]['historical_skos_candidate'],'broadMatch')
        self.assertEqual(edges[0]['decision_status'],'review_topology_without_gsim')

    def test_raw_bad_qualified_code_and_numeric_endpoint_both_survive(self):
        book={'ISIC4-5':[{'row':1,'cells':{'G':'Type of change in GSIM (blank means no change)'}},
                         correspondence_row(19,'0130','0130','VC1 - Code change',qualified='A013A0')]}
        with patch('atlas_sources.isic.read_workbook',return_value=book):
            edges,_=parse_correspondence({'raw':b'x','evidence':{}},[node('A','Rev.4'),node('0130','Rev.4')],
                                         [node('A','Rev.5'),node('0130','Rev.5')],[])
        self.assertEqual(edges[0]['from_code'],'0130')
        self.assertEqual(edges[0]['from_qualified_code'],'A013A0')
        self.assertIsNone(edges[0]['current_skos_candidate'])
        self.assertEqual(edges[0]['qualified_code_issues'][0]['expected_from_structure_and_numeric_column'],'A0130')

    def test_parent_note_update_defers_child_mapping(self):
        book={'ISIC4-5':[{'row':1,'cells':{'G':'Type of change in GSIM (blank means no change)'}}, correspondence_row(2,'0111','0111')]}
        with patch('atlas_sources.isic.read_workbook',return_value=book):
            edges,_=parse_correspondence({'raw':b'x','evidence':{}},[node('A','Rev.4'),node('0111','Rev.4')],
                                         [node('A','Rev.5'),node('0111','Rev.5')],[{'code':'A'}])
        self.assertEqual(edges[0]['historical_skos_candidate'],'exactMatch')
        self.assertIsNone(edges[0]['current_skos_candidate'])
        self.assertEqual(edges[0]['decision_status'],'review_2026_notes')

    def test_repeated_pair_does_not_overwrite_row_provenance(self):
        book={'ISIC4-5':[{'row':1,'cells':{'G':'Type of change in GSIM (blank means no change)'}},
                         correspondence_row(2,'0111','0111'), correspondence_row(3,'0111','0111')]}
        with patch('atlas_sources.isic.read_workbook',return_value=book):
            with self.assertRaisesRegex(ValueError,'duplicate correspondence pair'):
                parse_correspondence({'raw':b'x','evidence':{}},[node('A','Rev.4'),node('0111','Rev.4')],
                                     [node('A','Rev.5'),node('0111','Rev.5')],[])

    def test_notes_enrichment_cannot_change_source_parents(self):
        with self.assertRaises(ValueError):
            validate_enrichment([node('A','Rev.4'),node('0111','Rev.4')],
                                [node('A','Rev.4'),{**node('0111','Rev.4'),'parents':[]}])

    def test_code_format_does_not_strip_leading_zeroes(self):
        self.assertEqual(code_without_section('A0130'),'0130')
        with self.assertRaises(ValueError):
            code_without_section('A013A0')

    def test_research_decision_is_bound_to_reviewed_bytes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);p=root/'data/research/isic-review-decisions.json';p.parent.mkdir(parents=True)
            p.write_text(json.dumps({'reviewed_input_sha256':{'old':'changed'},'cases':[]}))
            with self.assertRaisesRegex(ValueError,'source bytes changed'):
                curate(root,[{'evidence':{'resource_id':'map','sha256':'a'}}],
                       [{'evidence':{'resource_id':'old','sha256':'b'}}],[{'evidence':{'resource_id':'new','sha256':'c'}}])


if __name__=='__main__':
    unittest.main()
