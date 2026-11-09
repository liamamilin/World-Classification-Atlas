"""Current CPC lighting evidence and separate WCO and UNSD historical records."""
import re
from html import escape

from .cpc_hs import LIGHTING_TITLE_ONLY, TABLE_I, TABLE_II
from .cpc_hs_followup import pdf_excerpt

DETAILS = {code: f"cpc3-detail-{code}-20261109" for code in ("46533", "46539", *LIGHTING_TITLE_ONLY)}
OLD_CHAPTER = "hs2017-chapter94"
MODULES_CHAPTER = "hs2022-chapter85"
REQUIRED = (*DETAILS.values(), OLD_CHAPTER, MODULES_CHAPTER)
LED_CLAUSE = "CPC:3.0:46533:HS2022:C:1"
LITERAL_CLAUSE = "CPC:3.0:46539:HS2022:C:1"
EXCLUSION_CLAUSE = "CPC:3.0:46539:HS2022:D:1"
OLD_ID = "HS:2017:9405.40"
OLD_TITLE = "Other electric lamps and lighting fittings"
CANDIDATES = {LED_CLAUSE: "HS:2022:9405.42", LITERAL_CLAUSE: "HS:2022:9405.49"}

# Old code as printed in Table I, page and line in Table I, page and source/target
# lines in Table II. The raw target is checked before attaching the legacy CPC row.
SCOPE_HISTORY = {
    "9405.19": (("ex9405.10", 33, 8, 23, 30, 32, "9405.19"),),
    "9405.29": (("ex9405.20", 33, 12, 23, 34, 36, "9405.29"),),
    "8539.51": (
        ("ex8539.90", 27, 41, 20, 8, 8, "ex8539.51"),
        ("ex8543.70", 27, 42, 20, 26, 26, "ex8539.51"),
        ("ex9405.10", 27, 43, 23, 30, 30, "ex8539.51"),
        ("ex9405.20", 27, 44, 23, 34, 34, "ex8539.51"),
        ("ex9405.30", 27, 45, 23, 38, 38, "ex8539.51"),
        ("ex9405.40", 27, 46, 23, 42, 42, "ex8539.51"),
    ),
    "8539.52": (("8539.50", 27, 48, 20, 5, 5, "8539.52"),),
}

ALLOCATION_FINDINGS = {
    "9405.19": ("46531", "source_broader", "current_title_scope",
                "CPC 标题明列天花板或墙壁电灯具，且同样排除公共开放场所或道路照明。HS 仅取该组的非 LED 专用残余项。"),
    "9405.29": ("46531", "source_broader", "current_title_scope",
                "CPC 标题明列电气台灯、书桌灯、床头灯和落地灯，未限定光源设计。HS 仅取该组的非 LED 专用残余项。"),
    "8539.51": ("46939", None, "historical_candidate",
                "旧 8543.70 的一部分转入 LED 模块，旧表将该码连至 CPC 2.1 的 46939。其余旧码来源不同，现行 46939 只作部分范围候选。46510 标题列的是灯丝灯、放电灯及弧光灯。"),
    "8539.52": ("46939", None, "historical_candidate",
                "WCO 两表将旧 LED 灯 8539.50 对应到 8539.52，UNSD 旧表将前者连到 CPC 2.1 的 46939。现行同码标题是其他电气设备，未点名 LED 灯。46510 标题列的是灯丝灯、放电灯及弧光灯。"),
}


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


def allocation_reviews(assets, hs_review, evidence, references):
    for rid, pages in ((TABLE_I, {27: (41, 48), 33: (6, 12)}), (TABLE_II, {20: (5, 26), 23: (30, 42)})):
        for page, (first, last) in pages.items():
            key = f"{rid}-p{page}-lighting"
            label = "打开 WCO 表 I" if rid == TABLE_I else "打开 WCO 表 II"
            evidence[key] = {**pdf_excerpt(assets, rid, page, first, last, ()), "label": label}
    legacy = hs_review["historical_cpc_hs"]
    legacy_by_hs = {}
    for rows in legacy["selected"].values():
        for row in rows:
            legacy_by_hs.setdefault(row["hs_id"], []).append(row)
    evidence["unsd-lighting-historical-csv"] = {**legacy["evidence"],
                                                "label": "下载 UNSD 历史对应 CSV"}
    official_targets = {target for ref in references.values() for target in ref["target_ids"]}
    reviews = {}
    for code, (cpc, relation, basis, finding) in ALLOCATION_FINDINGS.items():
        hs_id = f"HS:2022:{code}"
        if hs_id in official_targets:
            raise ValueError(f"new explicit CPC workbook reference for {hs_id}; reassess the scope review")
        history_rows = []
        for old, i_page, i_line, ii_page, ii_start, ii_line, new in SCOPE_HISTORY[code]:
            old_code = old.removeprefix("ex")
            old_id = f"HS:2017:{old_code}"
            first_key = f"{TABLE_I}-p{i_page}-lighting"
            second_key = f"{TABLE_II}-p{ii_page}-lighting"
            first = evidence[first_key]["text"].splitlines()
            first_offset = evidence[first_key]["lines"][0]
            first_row = first[i_line - first_offset].split()
            second = evidence[second_key]["text"].splitlines()
            second_offset = evidence[second_key]["lines"][0]
            second_start = second[ii_start - second_offset].split()
            second_row = second[ii_line - second_offset].split()
            if not (
                (first[0].split()[0] == code if code == "8539.51" else first_row[0] == code)
                and old in first_row and second_start[0] == old_code and second_row[-1] == new
            ):
                raise ValueError(f"changed WCO history for {old_id} → {hs_id}")
            history_rows.append({
                "id": f"{old_id}:WCO:{hs_id}", "hs_2017_id": old_id,
                "table_i": {"hs_2017": old, "hs_2022": code, "evidence_id": first_key, "line": i_line},
                "table_ii": {"hs_2017": old_code, "hs_2022": new, "evidence_id": second_key,
                             "line": ii_line, "source_line": ii_start},
                "historical_cpc21": legacy_by_hs[old_id],
            })
        proof = [f"cpc-{cpc}-workbook-title", f"cpc-{cpc}-pdf", f"cpc-{cpc}-online",
                 "unsd-cpc3-correspondence"]
        if cpc == "46939":
            proof.extend(("cpc-46510-workbook-title", "cpc-46510-pdf", "cpc-46510-online"))
        reviews[hs_id] = {"cpc_id": f"CPC:3.0:{cpc}", "relation": relation, "basis": basis,
                          "allocation_status": "pending", "finding": finding,
                          "evidence_ids": proof, "history": history_rows}
    return reviews


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
        if code in LIGHTING_TITLE_ONLY:
            workbook_row = hs_review["workbook_review_rows"][code]
            if (workbook_row["empty_note_columns"] != ["C", "D"] or note["text"] or
                    not re.search(r'<h4>Explanatory note</h4></div>\s*'
                                  r'(?:<div class="DtlCol2-[12] Dtl(?:Title|Cell)"></div>\s*){4}<br', html)):
                raise ValueError(f"CPC {code} no longer has title-only evidence")
            evidence[f"cpc-{code}-workbook-title"] = {
                **hs_review["workbook"], "sheet": "CPC3", "column": "B", "row": workbook_row["row"],
            }
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
    if not all(segment in by_code["46531"]["label"] for segment in (
        "electric ceiling or wall lighting fittings (except those for lighting public open spaces or thorough-fares)",
        "electric table, desk, bedside or floor-standing lamps",
    )):
        raise ValueError("CPC 46531 fixture scopes changed; review the title comparison")
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
        "allocation_reviews": allocation_reviews(assets, hs_review, evidence, references),
    }, evidence
