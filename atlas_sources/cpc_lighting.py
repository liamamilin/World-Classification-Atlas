"""Current CPC lighting evidence and the separate WCO split of HS 2017 9405.40."""
import re
from html import escape

from .cpc_hs import TABLE_I, TABLE_II
from .cpc_hs_followup import pdf_excerpt

DETAILS = {code: f"cpc3-detail-{code}-20261109" for code in ("46533", "46539")}
OLD_CHAPTER = "hs2017-chapter94"
MODULES_CHAPTER = "hs2022-chapter85"
REQUIRED = (*DETAILS.values(), OLD_CHAPTER, MODULES_CHAPTER)
LED_CLAUSE = "CPC:3.0:46533:HS2022:C:1"
LITERAL_CLAUSE = "CPC:3.0:46539:HS2022:C:1"
EXCLUSION_CLAUSE = "CPC:3.0:46539:HS2022:D:1"
OLD_ID = "HS:2017:9405.40"
OLD_TITLE = "Other electric lamps and lighting fittings"
CANDIDATES = {LED_CLAUSE: "HS:2022:9405.42", LITERAL_CLAUSE: "HS:2022:9405.49"}


def history(assets, hs_review):
    evidence = {
        "wco-2017-9405": pdf_excerpt(
            assets, OLD_CHAPTER, 3, 14, 25, ("94.05", "9405.40 - " + OLD_TITLE),
        ),
        "wco-lighting-table-i-9405": pdf_excerpt(
            assets, TABLE_I, 33, 18, 22, ("9405.41", "9405.42", "9405.49"),
        ),
        "wco-lighting-table-i-8539": pdf_excerpt(
            assets, TABLE_I, 27, 41, 46, ("8539.51", "ex9405.40"),
        ),
        "wco-lighting-table-ii": pdf_excerpt(
            assets, TABLE_II, 23, 42, 45, ("9405.40", "ex8539.51"),
        ),
        "unsd-hs2017-cpc21-lighting": {
            **hs_review["historical_cpc_hs"]["evidence"], "csv_line": 5730,
            "label": "下载 UNSD 历史对应 CSV · 第 5730 行",
        },
    }
    old_code = OLD_ID.rsplit(":", 1)[1]
    forward = [line.split() for line in evidence["wco-lighting-table-ii"]["text"].splitlines()]
    if forward != [[old_code, "ex8539.51"], ["9405.41"], ["9405.42"], ["9405.49"]]:
        raise ValueError("unexpected Table II split for HS 2017 9405.40")
    reverse = evidence["wco-lighting-table-i-9405"]["text"]
    reverse = [(number, *line.split()) for number, line in enumerate(reverse.splitlines(), 18) if line.strip()]
    if reverse != [(18, "9405.41", "ex9405.40"), (20, "9405.42", "ex9405.40"),
                   (22, "9405.49", "ex9405.40")]:
        raise ValueError("unexpected Table I lighting subheadings for HS 2017 9405.40")
    module_sources = re.findall(r"\bex\d{4}\.\d{2}\b", evidence["wco-lighting-table-i-8539"]["text"])
    if module_sources != ["ex8539.90", "ex8543.70", "ex9405.10", "ex9405.20", "ex9405.30", "ex9405.40"]:
        raise ValueError("unexpected Table I predecessors of HS 2022 8539.51")
    reverse = [(46, "8539.51", module_sources[-1]), *reverse]
    hs_ids = {node["id"] for node in hs_review["hs_structure"]["nodes"]}
    rows = []
    for table_ii_line, ((line, new_code, old_raw), target) in enumerate(zip(reverse, forward), 42):
        new_raw = target[-1]
        new_id = f"HS:2022:{new_code}"
        if new_id not in hs_ids or new_raw.removeprefix("ex") != new_code:
            raise ValueError(f"unmatched HS lighting split target: {new_raw}")
        rows.append({
            "id": f"{OLD_ID}:WCO:{new_id}", "hs_2022_id": new_id,
            "table_i": {"hs_2022": new_code, "hs_2017": old_raw, "line": line,
                        "evidence_id": "wco-lighting-table-i-8539" if new_code == "8539.51"
                        else "wco-lighting-table-i-9405"},
            "table_ii": {"hs_2017": old_code, "hs_2022": new_raw, "line": table_ii_line,
                         "evidence_id": "wco-lighting-table-ii"},
        })
    legacy = hs_review["historical_cpc_hs"]["selected"]["46539"]
    if legacy != [{"hs_id": OLD_ID, "cpc_id": "CPC:2.1:46539", "hs_partial": "0",
                   "cpc_partial": "0", "csv_line": 5730}]:
        raise ValueError("unexpected UNSD historical row for CPC 2.1 46539")
    return {
        "hs_2017": {"id": OLD_ID, "label": OLD_TITLE, "evidence_id": "wco-2017-9405"},
        "rows": rows, "hs2022_8539_51_table_i_predecessors": module_sources,
        "cpc21_hs2017": {**legacy[0], "evidence_id": "unsd-hs2017-cpc21-lighting"},
    }, evidence


def build(assets, by_code, hs_review, structure, notes, references):
    corrections = hs_review["scope_followup"]["corrigendum_audit"]
    split, evidence = history(assets, hs_review)
    evidence.update({
        "unsd-cpc3-corrections": corrections["evidence"][0],
        "unsd-cpc3-correspondence": {**hs_review["audit"]["listing"], "label": "打开 UNSD 对应表目录"},
        "cpc-46539-title": {**structure, "csv_row": by_code["46539"]["source_row"]},
    })
    expected = {
        LED_CLAUSE: ("9405.11", "9405.21", "9405.31", "9405.41"),
        LITERAL_CLAUSE: ("9405.42",),
        EXCLUSION_CLAUSE: ("9405.41",),
    }
    for code, resource_id in DETAILS.items():
        node, note, asset = by_code[code], notes[code], assets[resource_id]
        html = asset["raw"].decode("utf-8")
        statements = []
        for clause_id, codes in expected.items():
            if not clause_id.startswith(node["id"] + ":"):
                continue
            ref = references[clause_id]
            if ref["target_ids"] != [f"HS:2022:{target}" for target in codes]:
                raise ValueError(f"changed CPC lighting clause targets: {clause_id}")
            statements.append(ref["text"])
        if (
            not all(line in note["text"].splitlines() for line in statements)
            or not all(escape(value, quote=False) in html for value in (
                'id="PrintDivID"', f"Version 3.0 - Code {code}", node["label"], *statements,
            ))
            or html.count("HS 2022:") != len(statements)
        ):
            raise ValueError(f"CPC {code} PDF, workbook or online note changed; review LED scope")
        evidence[f"cpc-{code}-pdf"] = {**note["evidence"], "label": "打开 CPC 3.0 说明 PDF"}
        evidence[f"cpc-{code}-online"] = {**asset["evidence"], "element_id": "PrintDivID",
                                          "label": f"打开 UNSD 在线条目 {code} 快照"}
    if "not solely for LED light sources" not in by_code["46539"]["label"] or (
        "designed for use solely with light-emitting diode (LED) light sources" not in by_code["46533"]["label"]
    ):
        raise ValueError("CPC lighting titles changed; review LED scope")
    return {
        "status": "scope_conflict_pending", "cpc_id": by_code["46539"]["id"],
        "literal_clause_id": LITERAL_CLAUSE, "literal_hs_id": "HS:2022:9405.42",
        "excluded_clause_id": EXCLUSION_CLAUSE, "candidate_hs_id": CANDIDATES[LITERAL_CLAUSE],
        "candidate_basis": "CPC title and WCO residual subheading",
        "led_candidate": {"status": "pending", "cpc_id": by_code["46533"]["id"],
                          "hs_id": CANDIDATES[LED_CLAUSE], "checked_clause_id": LED_CLAUSE,
                          "basis": "CPC title and WCO LED-only subheading"},
        "correction_search": {"status": "no_46539_correction_in_checked_results",
                              "registry_last_update": corrections["registry_last_update"],
                              "result_ids": corrections["result_ids"]},
        "publication_status": hs_review["audit"]["status"],
        "evidence_ids": ["cpc-46539-title", "cpc-46539-pdf", "cpc-46539-online", "unsd-cpc3-corrections",
                         LITERAL_CLAUSE, EXCLUSION_CLAUSE, "wco-other-electric-lighting",
                         "cpc-46533-pdf", "cpc-46533-online", LED_CLAUSE, "unsd-cpc3-correspondence"],
        "hs_history": split,
    }, evidence
