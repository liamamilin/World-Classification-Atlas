"""Publisher snapshots and WCO scope evidence for four CPC reference clauses."""
import re

from .acquire import sha256
from .hs import pdf_lines

CORRECTIONS = "cpc3-corrections-register-20261109"
CORRECTION_4379 = "cpc3-correction-4379"
OCTOPUS_DETAIL = "cpc3-detail-21267-20261109"
ENERGY_MANUAL = "siec1-escm-historical-coal"
RULES = "hs2022-wco-interpretation-rules"
REQUIRED = (CORRECTIONS, CORRECTION_4379, OCTOPUS_DETAIL, ENERGY_MANUAL, RULES)
HISTORICAL_CODES = {"11010", "11030", "21267", "49913"}

# Each excerpt retains its physical PDF page, pdftotext -layout lines and digest.
WCO = {
    "HS:2022:0307:WCO:octopus": (
        "无独立数字码的章鱼分组", "dash_group", ("0307", "0307.51", "0307.52", "0307.59"),
        ("0307.51", "0307.52", "0307.59"),
        (("hs2022-chapter03", 11, 23, 26, ("- Octopus (Octopus spp.)", "0307.51", "0307.52", "0307.59", "-- Frozen")),),
    ),
    "HS:2022:03:WCO:chapter-note-1c": (
        "第 03 章章注 1(c) · 不适合人食用的粉、粗粉或团粒", "chapter_note",
        ("03", "0307", "0307.52", "0307.59", "2301"), ("2301",),
        (("hs2022-chapter03", 1, 10, 13, ("unfit or unsuitable", "unfit for human consumption (heading 23.01)")),),
    ),
    "HS:2022:03:WCO:chapter-note-3": (
        "第 03 章章注 3 · 供人食用的粉、粗粉或团粒", "chapter_note",
        ("03", "0307", "0307.52", "0307.59", "0309", "0309.90"), ("0309", "0309.90"),
        (("hs2022-chapter03", 1, 17, 18, ("03.05 to 03.08 do not cover", "heading 03.09")),
         ("hs2022-chapter03", 12, 24, 27, ("03.09", "0309.10", "0309.90", "- Of fish", "- Other"))),
    ),
    "HS:2022:2701:WCO:unagglomerated-coal": (
        "无独立数字码的未团聚煤分组", "dash_group",
        ("2701", "2701.11", "2701.12", "2701.19", "2701.20"),
        ("2701.11", "2701.12", "2701.19"),
        (("hs2022-chapter27", 2, 3, 9, ("- Coal, whether or not pulverised, but not agglomerated",
                                       "2701.11", "2701.12", "2701.19", "2701.20")),),
    ),
    "HS:2022:27:WCO:subheading-note-2": (
        "第 27 章子目注 2 · 烟煤阈值", "subheading_note", ("27", "2701", "2701.12"), ("2701.12",),
        (("hs2022-chapter27", 1, 33, 35,
          ("2701.12", "a dry, mineral-matter-free basis", "exceeding 14 %", "a moist, mineral-matter-", "5,833 kcal/kg")),),
    ),
    "HS:2022:2702:WCO:lignite": (
        "27.02 褐煤品目", "heading", ("2701.12", "2702", "2702.10", "2702.20"), ("2702.10", "2702.20"),
        (("hs2022-chapter27", 2, 11, 13, ("27.02", "Lignite", "2702.10", "2702.20")),),
    ),
    "HS:2022:8711:WCO:heading": (
        "87.11 品目及同级子目", "heading",
        ("8711", "8711.10", "8711.20", "8711.30", "8711.40", "8711.50", "8711.60", "8711.90"),
        ("8711.10", "8711.20", "8711.30", "8711.40", "8711.50", "8711.60", "8711.90"),
        (("hs2022-chapter87", 4, 39, 46, ("87.11", "with or without side-cars; side-cars", "8711.10", "8711.30")),
         ("hs2022-chapter87", 5, 3, 8, ("8711.40", "8711.50", "8711.60", "With electric motor for propulsion", "8711.90", "- Other"))),
    ),
    "HS:2022:87:WCO:chapter-note-4": (
        "第 87 章章注 4 · 儿童自行车与其他儿童车边界", "chapter_note",
        ("87", "8711", "8711.60", "8711.90", "8712.00", "9503"), ("8712.00", "9503"),
        (("hs2022-chapter87", 1, 16, 22, ("87.12 includes all children's bicycles", "95.03", "Subheading 8708.22")),
         ("hs2022-chapter87", 5, 10, 11, ("87.12", "8712.00", "motorised."))),
    ),
    "HS:2022:WCO:GIR:6": (
        "WCO 归类总规则 6 · 同级子目比较", "interpretation_rule",
        ("0307.52", "2701.12", "8711.60", "8711.90"), (),
        ((RULES, 1, 46, 50, ("only subheadings at the same level", "Section and Chapter Notes")),),
    ),
}

OCTOPUS_WCO = ("HS:2022:0307:WCO:octopus", "HS:2022:03:WCO:chapter-note-1c", "HS:2022:03:WCO:chapter-note-3")
COAL_WCO = ("HS:2022:2701:WCO:unagglomerated-coal", "HS:2022:27:WCO:subheading-note-2", "HS:2022:2702:WCO:lignite")
MOTORCYCLE_WCO = ("HS:2022:8711:WCO:heading", "HS:2022:87:WCO:chapter-note-4", "HS:2022:WCO:GIR:6")
CASES = {
    "CPC:3.0:21267:HS2022:C:1": (OCTOPUS_WCO, "21267"),
    "CPC:3.0:11012:HS2022:C:1": (COAL_WCO, "11010"),
    "CPC:3.0:11031:HS2022:C:1": (COAL_WCO, "11030"),
    "CPC:3.0:49913:HS2022:C:1": (MOTORCYCLE_WCO, "49913"),
}


def pdf_excerpt(assets, rid, page, first, last, markers):
    excerpt = "\n".join(pdf_lines(assets, rid, page)[first - 1:last])
    if not all(marker in " ".join(excerpt.split()) for marker in markers):
        raise ValueError(f"source passage changed: {rid} p{page} lines {first}–{last}")
    return {**assets[rid]["evidence"], "pdf_page": page, "lines": [first, last],
            "text_sha256": sha256(excerpt.encode("utf-8")), "text": excerpt}


def audit_octopus(assets):
    filtered = assets[CORRECTIONS]["raw"].decode("utf-8")
    positive = assets[CORRECTION_4379]["raw"].decode("utf-8")
    detail = assets[OCTOPUS_DETAIL]["raw"].decode("utf-8")
    for field in ("CPC", "2100", "Correction"):
        if not re.search(rf'<option value="{field}"\s+selected(?:=selected)?>', filtered):
            raise ValueError(f"CPC correction search filter not applied: {field}")
    table = re.search(r'<table id="example"[^>]*>.*?</table>', filtered, re.S)
    updated = re.search(r"Registry last update:</b>\s*(\d{4}-\d{2}-\d{2})", filtered)
    if not table or not updated:
        raise ValueError("CPC correction result table or date not found")
    rows = re.findall(r'/Registry/Detail/(\d+)"', table[0])
    if rows != ["4379"] or "15 Apr 2026" not in table[0] or "A Typo in CPC Ver. 3.0" not in table[0]:
        raise ValueError("CPC 3.0 correction results differ from reviewed snapshot")
    if not all(value in positive for value in (
        "4379</div>", "/EN/2100/03239", "2 July 2026", "edible edible",
    )):
        raise ValueError("UNSD correction 4379 is missing the reviewed code, date or decision")
    if not all(value in detail for value in (
        "Version 3.0 - Code 21267", "HS 2022: 0307.53 and 0307.59", "flours, meals and pellets of octopus",
    )):
        raise ValueError("UNSD online octopus note differs from reviewed snapshot")
    return {
        "status": "no_octopus_correction_in_checked_cpc3_registry_results",
        "registry_last_update": updated[1], "result_ids": rows,
        "positive_control": {"id": "4379", "cpc_id": "CPC:3.0:03239",
                             "listing_date": "2026-04-15", "detail_updated": "2026-07-02"},
        "online_cpc_id": "CPC:3.0:21267", "printed_hs2022_codes": ["0307.53", "0307.59"],
        "candidate_hs_id": "HS:2022:0307.52",
        "evidence": [
            {**assets[CORRECTIONS]["evidence"], "element_id": "searchResult", "label": "打开 UNSD 更正检索结果",
             "search_form": assets[CORRECTIONS]["resource"]["search_form"]},
            {**assets[CORRECTION_4379]["evidence"], "element_id": "PrintDivID", "label": "打开 UNSD 更正 4379 原件"},
            {**assets[OCTOPUS_DETAIL]["evidence"], "element_id": "PrintDivID", "label": "打开 UNSD 在线条目 21267 快照"},
        ],
    }


def build(assets, references, nodes):
    by_code = {node["code"]: node["id"] for node in nodes}
    wco_evidence = {}
    for key, (label, kind, subjects, related, passages) in WCO.items():
        wco_evidence[key] = {
            "label": label, "kind": kind, "subject_ids": [by_code[code] for code in subjects],
            "related_hs_ids": [by_code[code] for code in related],
            "passages": [pdf_excerpt(assets, *passage) for passage in passages],
        }
    by_ref = {ref["id"]: ref for ref in references}
    expected = {
        "CPC:3.0:21267:HS2022:C:1": ("0307.59",),
        "CPC:3.0:11012:HS2022:C:1": ("2701.12",),
        "CPC:3.0:11031:HS2022:C:1": ("2701.12",),
        "CPC:3.0:49913:HS2022:C:1": ("8711.60", "8711.90"),
    }
    for ref_id, codes in expected.items():
        if by_ref[ref_id]["target_ids"] != [by_code[code] for code in codes]:
            raise ValueError(f"reviewed CPC reference targets changed: {ref_id}")
    return {
        "corrigendum_audit": audit_octopus(assets), "wco_evidence": wco_evidence,
        "historical_coal": pdf_excerpt(
            assets, ENERGY_MANUAL, 47, 5, 20, ("Annex 3A", "CPC, Ver. 2.1", "HS 2017",
                                                "0210 Sub-bituminous coal", "2702.10*", "2701.12"),
        ),
        "by_reference": {ref_id: {"wco_ids": list(wco_ids), "historical_cpc21_code": old_code}
                         for ref_id, (wco_ids, old_code) in CASES.items()},
    }
