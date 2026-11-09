"""Traceable CPC notes, selected HS evidence and edition-specific correspondence."""
import csv
import io
import re
import subprocess
from collections import Counter

from .acquire import sha256
from .xlsx import read_workbook

WORKBOOK = "cpc3-notes-xlsx-20250630"
LISTING = "cpc3-correspondence-listing-20261109"
STATUS = "cpc3-hs2022-status-202605"
CHAPTER = "hs2022-chapter68"
GUIDANCE = "hs2022-wco-who-medical-supplies"
TABLE_I = "hs2022-to-hs2017-wco-table-i"
TABLE_II = "hs2017-to-hs2022-wco-table-ii"
LEGACY = "cpc21-hs2017-unsd-correspondence"
REQUIRED = (WORKBOOK, LISTING, STATUS, CHAPTER, GUIDANCE, TABLE_I, TABLE_II, LEGACY)

HS_SCOPE = {
    "4818.90": ("纸或纤维素口罩示例（多数国家）", GUIDANCE, 3, 9, 11, "Cellulose/paper masks"),
    "6307.90": ("无机械部件或可更换滤芯的纺织口罩示例", GUIDANCE, 3, 12, 16, "Textile face-masks"),
    "9020.00": ("带机械部件或可更换滤芯的防毒面具示例", GUIDANCE, 3, 18, 20, "Gas masks with mechanical parts"),
    "6815.11": ("碳纤维本体", CHAPTER, 4, 35, 35, "Carbon fibres"),
    "6815.12": ("碳纤维织物", CHAPTER, 4, 36, 36, "Fabrics of carbon fibres"),
    "6815.13": ("其他碳纤维制品（该组限非电气用途）", CHAPTER, 4, 37, 37, "Other articles of carbon fibres"),
    "6815.19": ("该非电气用组中的其他项", CHAPTER, 4, 38, 38, "-- Other"),
}
# Atlas scope findings. Each HS code is a route to separate evidence; CPC links keep their own status.
REVIEWS = {
    "48160": [
        ("6307.90", "excluded_from_cpc", "同时无机械部件和可换滤芯的防护口罩明确排除；WCO 的纺织口罩示例提供边界旁证。"),
        ("4818.90", "scope_boundary", "排除条款没有指定材料。WCO 另列纸或纤维素口罩，注明多数国家的归类及需确认的情形。"),
        ("9020.00", "pending", "WCO 对带机械部件或可换滤芯的防毒面具提供正向示例。当前两版的直接代码对应待核。"),
    ],
    "27190": [
        ("6307.90", "pending", "纺织口罩是有历史对应支持的候选。CPC 3.0 标题未点名口罩，说明工作簿的纳入与排除单元格为空。"),
    ],
    "37990": [
        ("6815.11", "pending", "碳纤维本体在 HS 单列。当前 CPC 的残余范围未逐项确认。"),
        ("6815.12", "pending", "HS 单列碳纤维织物。CPC 标题仅给出非电气用碳制品的较宽范围，织物具体归属待核。"),
        ("6815.13", "pending", "HS 区分其他非电气用碳纤维制品和织物。具体制品的 CPC 归属待核。"),
        ("6815.19", "scope_boundary", "这是同一 HS 组的其他项。历史 6815.10 的对应代码列指向该项。"),
    ],
    "46950": [
        ("6815.13", "scope_boundary", "CPC 46950 的电气用范围与这组 HS 6815 的非电气用边界分开。旧表列 HS 8545，具体电气制品的当前对应待核。"),
    ],
    "89200": [
        (None, "service_context", "原文涵盖受托塑料件制造服务，可包含碳纤维增强。产出制品的产品子类及 HS 归属待核。"),
    ],
}


def pdf_lines(assets, rid, page):
    return subprocess.check_output([
        "pdftotext", "-f", str(page), "-l", str(page), "-layout", str(assets[rid]["path"]), "-"
    ]).decode("utf-8").split("\f", 1)[0].splitlines()


def workbook_references(asset, by_code):
    sheet = "CPC3"
    rows = read_workbook(asset["raw"])[sheet]
    fields = rows[0]["cells"]
    if list(fields) != list("ABCD") or not (
        fields["C"].endswith(" - Inclusions") and fields["D"].endswith(" - Exclusions")
    ):
        raise ValueError("unexpected CPC 3.0 note workbook columns")
    if [r["cells"]["A"] for r in rows[1:]] != list(by_code):
        raise ValueError("CPC 3.0 note workbook and CSV code sequences differ")
    references = []
    for row in rows[1:]:
        cells = row["cells"]
        cpc_id = by_code[cells["A"]]["id"]
        for column in "CD":
            for number, line in enumerate((cells.get(column) or "").splitlines(), 1):
                if "HS 2022:" not in line:
                    continue
                kind = "exclusion" if column == "D" else "inclusion"
                if column == "C" and line.startswith("This subclass is defined through"):
                    kind = "definition"
                notation = re.split(r"\s+and includes:|\)", line.split("HS 2022:", 1)[1], maxsplit=1)[0]
                references.append({
                    "cpc_id": cpc_id, "hs_edition": "2022", "kind": kind,
                    "hs_notation": notation.strip().rstrip("."), "sheet": sheet,
                    "row": row["row"], "column": column, "line": number,
                    "text_sha256": sha256(line.encode("utf-8")), "text": line,
                })
    selected = {r["cells"]["A"]: r for r in rows[1:] if r["cells"]["A"] in REVIEWS}
    checked = {
        code: {"row": row["row"], "explicit_hs2022_reference": any(
                   ref["cpc_id"] == by_code[code]["id"] for ref in references),
               "empty_note_columns": [col for col in "CD" if not row["cells"].get(col)]}
        for code, row in selected.items()
    }
    return references, checked


def publication_audit(assets):
    html = assets[LISTING]["raw"].decode("utf-8")
    table = re.search(r'id="corresp-cpc".*?<table\b[^>]*>(.*?)</table>', html, re.S)
    if table is None:
        raise ValueError("publisher correspondence matrix not found")
    matrix = re.sub(r"<!--.*?-->", "", table[1], flags=re.S)
    labels = re.findall(r"<strong>([^<>]+)</strong>", matrix)
    links = re.findall(r'<a href="([^"]+)"', matrix)
    if "CPC Ver. 2.1" not in labels or "HS2017" not in labels or not any(
        link.endswith("/CPC21-HS2017.csv") for link in links
    ):
        raise ValueError("expected CPC 2.1 / HS 2017 positive control missing from correspondence listing")
    if re.search(r"CPC\s*(?:Ver\.\s*|v)?3\.?0?|HS\s*2022", matrix, re.I):
        raise ValueError("publisher correspondence matrix changed; review CPC 3.0 and HS 2022 availability")
    slide = pdf_lines(assets, STATUS, 46)
    if not any("Correspondence table: work in progress" in line for line in slide) or not any(
        "CPC Ver. 3.0 and HS 2022" in line for line in slide
    ):
        raise ValueError("expected CPC 3.0 / HS 2022 workshop statement missing")
    return {
        "status": "standalone_table_not_located_in_checked_listing",
        "listing": {**assets[LISTING]["evidence"], "element_id": "corresp-cpc", "labels": labels,
                    "link_count": len(links)},
        "workshop": {**assets[STATUS]["evidence"], "pdf_page": 46},
    }


def carbon_correlations(assets):
    first = pdf_lines(assets, TABLE_I, 17)
    second = pdf_lines(assets, TABLE_II, 11)
    if not any(re.search(r"2022 Version\s+2017 Version\s+Remarks", line) for line in first) or not any(
        re.search(r"2017 Version\s+2022 Version", line) for line in second
    ):
        raise ValueError("HS correlation table column order changed")
    reverse = {}
    old = None
    for number, line in enumerate(second, 1):
        # The PDF's second column includes continuation lines without a new left code.
        left, right = line[:60].strip(), line[60:].strip()
        if left:
            old = left
        if old in {"6815.10", "6815.99"} and re.fullmatch(r"(?:ex)?6815\.\d{2}", right):
            reverse[(old, right)] = number
    rows = {}
    for number, line in enumerate(first, 1):
        match = re.match(r"\s*(6815\.(?:11|12|13|19))\s+((?:ex)?6815\.\d{2})(?:\s|$)", line)
        if not match:
            continue
        code, old_raw = match.groups()
        old_code = old_raw.removeprefix("ex")
        rows[code] = {
            "table_i": {"hs_2022": code, "hs_2017": old_raw, "line": number},
            "table_ii": {"hs_2017": old_code, "hs_2022": code, "line": reverse[(old_code, code)]},
            "hs2017_partial_in_table_i": old_raw.startswith("ex"),
        }
    if set(rows) != {"6815.11", "6815.12", "6815.13", "6815.19"} or "has been subdivided" not in first[37]:
        raise ValueError("expected four HS carbon correlation rows and shared remark")
    return {
        "rows": rows,
        "table_i": {**assets[TABLE_I]["evidence"], "pdf_page": 17, "remark_lines": [38, 41]},
        "table_ii": {**assets[TABLE_II]["evidence"], "pdf_page": 11},
    }


def legacy_correspondences(asset):
    rows = csv.DictReader(io.StringIO(asset["raw"].decode("utf-8-sig"), newline=""))
    if rows.fieldnames != ["HS 2017", "HS partial", "CPC Ver. 2.1", "CPC partial"]:
        raise ValueError("unexpected historical correspondence CSV header")
    count, selected = Counter(), {}
    for row in rows:
        hs, cpc = row["HS 2017"], row["CPC Ver. 2.1"]
        hs_partial, cpc_partial = row["HS partial"], row["CPC partial"]
        if not re.fullmatch(r"\d{4}\.\d{2}", hs) or not re.fullmatch(r"\d{5}", cpc) or (
            hs_partial not in {"0", "1"} or cpc_partial not in {"0", "1"}
        ):
            raise ValueError(f"invalid historical correspondence at CSV line {rows.line_num}")
        count[f"HS={hs_partial};CPC={cpc_partial}"] += 1
        if cpc in REVIEWS or cpc == "32193" and hs == "4818.90":
            selected.setdefault(cpc, []).append({
                "hs_id": f"HS:2017:{hs}", "cpc_id": f"CPC:2.1:{cpc}",
                "hs_partial": hs_partial, "cpc_partial": cpc_partial, "csv_line": rows.line_num,
            })
    return {"by_flags": dict(count), "rows": sum(count.values()), "selected": selected,
            "evidence": asset["evidence"]}


def build(assets, by_code):
    references, checked = workbook_references(assets[WORKBOOK], by_code)
    if any(row["explicit_hs2022_reference"] for row in checked.values()):
        raise ValueError("a reviewed CPC scope has new explicit HS 2022 evidence; reassess the review")
    hs = {}
    for code, (label, rid, page, start, end, marker) in HS_SCOPE.items():
        lines = pdf_lines(assets, rid, page)[start - 1:end]
        source_text = "\n".join(lines)
        if code not in source_text or marker not in source_text:
            raise ValueError(f"HS 2022 {code} source location mismatch")
        hs[code] = {
            "id": f"HS:2022:{code}", "label": label, "source_kind": assets[rid]["resource"]["role"],
            "evidence": {**assets[rid]["evidence"], "pdf_page": page, "lines": [start, end],
                         "text_sha256": sha256(source_text.encode("utf-8"))},
        }
    heading = next(r for r in references if r["cpc_id"] == "CPC:3.0:32193" and r["hs_notation"] == "4818"
                   and r["kind"] == "definition")
    hs["4818"] = {"id": "HS:2022:4818", "label": "CPC 3.0 注释引用的品目",
                  "source_kind": "official_cpc_note", "note_cpc_id": heading["cpc_id"]}
    reviews = {
        code: [{"hs_id": hs[hs_code]["id"] if hs_code else None, "status": status, "finding": finding}
               for hs_code, status, finding in findings]
        for code, findings in REVIEWS.items()
    }
    return {
        "audit": publication_audit(assets), "workbook": assets[WORKBOOK]["evidence"],
        "workbook_code_rows": len(by_code), "official_note_references": references,
        "workbook_review_rows": checked, "hs": hs, "reviews": reviews,
        "carbon_correlations": carbon_correlations(assets), "historical_cpc_hs": legacy_correspondences(assets[LEGACY]),
    }
