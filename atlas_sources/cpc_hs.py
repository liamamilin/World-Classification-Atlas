"""Traceable CPC notes, selected HS evidence and edition-specific correspondence."""
import csv
import io
import re
from collections import Counter

from . import cpc_hs_followup, hs, hs_reference
from .acquire import sha256
from .hs import pdf_lines
from .xlsx import read_workbook

WORKBOOK = "cpc3-notes-xlsx-20250630"
LISTING = "cpc3-correspondence-listing-20261109"
STATUS = "cpc3-hs2022-status-202605"
CHAPTER = "hs2022-chapter68"
GUIDANCE = "hs2022-wco-who-medical-supplies"
TABLE_I = "hs2022-to-hs2017-wco-table-i"
TABLE_II = "hs2017-to-hs2022-wco-table-ii"
LEGACY = "cpc21-hs2017-unsd-correspondence"
REVIEW_CHAPTERS = ("03", "27", "30", "87", "94")
REQUIRED = (WORKBOOK, LISTING, STATUS, CHAPTER, GUIDANCE, TABLE_I, TABLE_II, LEGACY,
            hs.STRUCTURE, hs.CONTENTS, *(f"hs2022-chapter{code}" for code in REVIEW_CHAPTERS),
            *cpc_hs_followup.REQUIRED)

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

NOTE_REVIEWS = {
    ("11012", "C"): ("scope_pending", "烟煤 11012 与次烟煤 11031 均引用 2701.12。WCO 子目注 2 同时要求挥发分在干燥无矿物质基准上超过 14%，热值在含水无矿物质基准上至少 5,833 kcal/kg。CPC 共引范围待核。",
                    "27", 1, ("2701.12",), None),
    ("11031", "C"): ("scope_pending", "次烟煤 11031 位于褐煤类，烟煤 11012 位于硬煤类，两者共引 2701.12。WCO 对该子目的烟煤阈值明确，CPC 共引范围及次烟煤对应仍待核。",
                    "27", 1, ("2701.12",), None),
    ("21267", "C"): ("missing_code", "CPC 工作簿、说明 PDF 和在线条目均写 0307.53。UNSD 更正检索只返回与章鱼无关的 4379 号。WCO 分组列 0307.52 为冷冻章鱼，Atlas 保留该码为待核候选。CPC 同时涵盖供人食用的章鱼粉、粗粉和团粒，WCO 章注将这类制品划到 03.09，具体跨表范围待核。",
                    "03", 11, ("0307.52", "0307.59"), "0307.52"),
    ("35272", "C"): ("scope_pending", "3002.90 是该 HS 品目的其他项，原引用可回查，残余子目与 CPC 血液和免疫产品条目的范围待核。",
                    "30", 3, ("3002.90",), None),
    ("35273", "C"): ("notation_reviewed", "3002.41–49 取税则中存在的三个子目，3002.51/59 保留为并列的两个子目。",
                    "30", 3, ("3002.41", "3002.42", "3002.49", "3002.51", "3002.59"), None),
    ("41609", "C"): ("notation_reviewed", "8105.30 后的句点用于分隔紧邻的两个完整代码，HS 工作表中两者各为独立的废料子目。",
                    None, None, (), None),
    ("46532", "D"): ("scope_reviewed", "9405.31 在此处为排除，在 CPC 46533 是定义引用。",
                    "94", 4, ("9405.31",), None),
    ("46533", "C"): ("notation_reviewed", "裸后缀 31 和 41 沿用 9405。原句列出四个 LED 专用子目，9405.42 未列在此处。",
                    "94", 4, ("9405.21", "9405.31", "9405.41"), None),
    ("46539", "C"): ("scope_pending", "CPC 标题限定非 LED 专用，定义句引用的 9405.42 在 WCO 税则中限定 LED 专用。保留官方引用，范围对应待核。9405.49 是同组残余项，Atlas 单列候选。",
                    "94", 4, ("9405.41", "9405.42", "9405.49"), None),
    ("46539", "D"): ("scope_reviewed", "9405.41 在此处为排除，在 CPC 46533 是定义引用。",
                    "94", 4, ("9405.41",), None),
    ("49913", "C"): ("scope_pending", "纳入句点名电驱动并引用两个代码。WCO 将电驱动列入 8711.60，8711.90 是品目 87.11 的同级残余项。CPC 类标题另含边车，8711.90 的具体范围待核。",
                    "87", 5, ("8711.60", "8711.90"), None),
}


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
                    "id": f"{cpc_id}:HS2022:{column}:{number}",
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
        if cpc in REVIEWS or cpc in cpc_hs_followup.HISTORICAL_CODES or (cpc == "32193" and hs == "4818.90"):
            selected.setdefault(cpc, []).append({
                "hs_id": f"HS:2017:{hs}", "cpc_id": f"CPC:2.1:{cpc}",
                "hs_partial": hs_partial, "cpc_partial": cpc_partial, "csv_line": rows.line_num,
            })
    return {"by_flags": dict(count), "rows": sum(count.values()), "selected": selected,
            "evidence": asset["evidence"]}


def attach_note_reviews(assets, references, nodes):
    hs_codes = {node["code"]: node["id"] for node in nodes}
    located = set()
    for ref in references:
        key = (ref["cpc_id"].rsplit(":", 1)[1], ref["column"])
        if key not in NOTE_REVIEWS:
            continue
        status, finding, chapter, page, markers, candidate = NOTE_REVIEWS[key]
        review = {"status": status, "finding": finding}
        if chapter:
            rid = f"hs2022-chapter{chapter}"
            lines = pdf_lines(assets, rid, page)
            hits = [number for number, line in enumerate(lines, 1) if any(code in line for code in markers)]
            if not all(any(code in line for line in lines) for code in markers):
                raise ValueError(f"HS chapter {chapter} verification marker missing")
            review["evidence"] = {**assets[rid]["evidence"], "pdf_page": page, "lines": hits}
        if candidate:
            review["candidate_hs_id"] = hs_codes[candidate]
        ref["review"] = review
        located.add(key)
    if located != set(NOTE_REVIEWS):
        raise ValueError("CPC note review points to missing references")


def build(assets, by_code):
    references, checked = workbook_references(assets[WORKBOOK], by_code)
    if any(row["explicit_hs2022_reference"] for row in checked.values()):
        raise ValueError("a reviewed CPC scope has new explicit HS 2022 evidence; reassess the review")
    structure = hs.catalogue(assets)
    hs_reference.resolve(references, structure["nodes"])
    attach_note_reviews(assets, references, structure["nodes"])
    scope = {}
    for code, (label, rid, page, start, end, marker) in HS_SCOPE.items():
        lines = pdf_lines(assets, rid, page)[start - 1:end]
        source_text = "\n".join(lines)
        if code not in source_text or marker not in source_text:
            raise ValueError(f"HS 2022 {code} source location mismatch")
        scope[code] = {
            "label": label, "source_kind": assets[rid]["resource"]["role"],
            "evidence": {**assets[rid]["evidence"], "pdf_page": page, "lines": [start, end],
                         "text_sha256": sha256(source_text.encode("utf-8"))},
        }
    if set(scope) - {node["code"] for node in structure["nodes"]}:
        raise ValueError("HS scope review points outside HS 2022 catalogue")
    reviews = {
        code: [{"hs_id": f"HS:2022:{hs_code}" if hs_code else None, "status": status, "finding": finding}
               for hs_code, status, finding in findings]
        for code, findings in REVIEWS.items()
    }
    targets = [target for ref in references for target in ref["target_ids"]]
    reference_counts = {
        "by_kind": dict(Counter(ref["kind"] for ref in references)),
        "by_resolution": dict(Counter(ref["resolution_status"] for ref in references)),
        "terms_by_form": dict(Counter(term["form"] for ref in references for term in ref["terms"])),
        "resolved_links": len(targets), "unique_hs_targets": len(set(targets)),
        "links_by_kind": {kind: sum(len(ref["target_ids"]) for ref in references if ref["kind"] == kind)
                          for kind in ("definition", "inclusion", "exclusion")},
    }
    return {
        "audit": publication_audit(assets), "workbook": assets[WORKBOOK]["evidence"],
        "workbook_code_rows": len(by_code), "official_note_references": references,
        "official_note_reference_counts": reference_counts,
        "workbook_review_rows": checked, "hs_structure": structure, "hs_scope": scope, "reviews": reviews,
        "carbon_correlations": carbon_correlations(assets), "historical_cpc_hs": legacy_correspondences(assets[LEGACY]),
        "scope_followup": cpc_hs_followup.build(assets, references, structure["nodes"]),
    }
