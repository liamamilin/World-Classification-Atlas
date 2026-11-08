"""Auxiliary product evidence and explicit follow-ups to unresolved activity scopes."""
import copy
import re
from .acquire import sha256
from .registry import read_json, write_json
from .xlsx import read_workbook

SELECTED = {"17400", "22270", "26890", "27190", "37990", "46950", "48160"}


def read_cpc21(asset):
    book = read_workbook(asset["raw"])
    rows = book["CPC2.1"]
    expected = ["CPC Ver. 2.1 Code", "CPC Ver. 2.1 Title", "CPC Ver. 2.1 Explanatory Note - Inclusions",
                "CPC Ver. 2.1 Explanatory Note - Exclusions"]
    if list(rows[0]["cells"].values()) != expected:
        raise ValueError("CPC2.1 corrected workbook header changed")
    codes, selected = set(), []
    for row in rows[1:]:
        c = row["cells"];code = c.get("A")
        if not isinstance(code, str) or not re.fullmatch(r"\d{1,5}", code) or code in codes:
            raise ValueError("invalid or duplicate CPC2.1 main-sheet code")
        codes.add(code)
        if code in SELECTED:
            selected.append({"id": "CPC:2.1:" + code, "code": code, "label": c["B"],
                             "classification_object": "products and services", "component": "corrected_notes_2025-04-03",
                             "notes": {"includes": c.get("C"), "excludes": c.get("D")}, "original_fields": row,
                             "evidence": {**asset["evidence"], "sheet": "CPC2.1", "row": row["row"],
                                          "range": f"A{row['row']}:D{row['row']}"}})
    if {n["code"] for n in selected} != SELECTED:
        raise ValueError("missing CPC boundary evidence subclass")
    return selected, book, {"main_sheet_code_rows": len(codes), "selected_subclasses": len(selected),
                            "trade_template_rows_not_expanded": len(book["61_62"]),
                            "use": "auxiliary product evidence; not an economic-activity scheme or equivalence"}


def correspondence_rows(pages, valid_isic_codes, selected=SELECTED):
    result = {}
    pattern = re.compile(r"^\s*(?:\d{4}\s+)?(\d{5})\s+.+\s+(\d{4})\s*$")
    for page in pages:
        # These are the manual's detailed-structure tables, before explanatory notes.
        if not 40 <= page["pdf_page"] <= 150 or "ISIC 4" not in page["text"]:
            continue
        offset = 0
        for number, line in enumerate(page["text"].splitlines(keepends=True), 1):
            m = pattern.match(line.rstrip("\r\n"))
            if m and m[1] in selected:
                code, industry = m.groups()
                if code in result or industry not in valid_isic_codes:
                    raise ValueError("duplicate or invalid auxiliary CPC/ISIC table row")
                result[code] = {"id": "CPC21-ISIC4:" + code, "product_code": code, "industry_code": industry,
                                "from_scheme": "CPC2.1", "to_scheme": "ISIC Rev.4", "origin": "official_manual_table",
                                "relation": None, "semantic_equivalence": False,
                                "evidence": {**page["evidence"], "line": number, "start": offset,
                                             "end": offset + len(line.rstrip("\r\n")),
                                             "text_sha256": sha256(line.rstrip("\r\n").encode())}}
            offset += len(line)
    if set(result) != set(selected):
        raise ValueError("selected auxiliary CPC/ISIC correspondence coverage incomplete")
    return list(result.values())


def auxiliary(root, assets, pdf_documents, old):
    nodes, workbook, stats = read_cpc21(assets["cpc21-notes-20250403"])
    links = correspondence_rows(pdf_documents["cpc21-manual-2015"], {n["code"] for n in old})
    output = root / "data/local/economy/isic"
    write_json(output / "cpc21-selected-evidence.json", nodes)
    write_json(output / "cpc21-source-workbook.json", workbook)
    write_json(output / "cpc21-isic4-selected-correspondence.json", links)
    write_json(root / "data/reports/cpc-boundary-evidence.json", {"statistics": stats, "correspondences": links})
    return {n["id"]: n for n in nodes}, stats


def extend_plan(root, original):
    path = root / "data/research/isic-boundary-review.json"
    followup = read_json(path)
    if sha256((root / "data/research/isic-priority-review.json").read_bytes()) != followup["parent_priority_sha256"]:
        raise ValueError("boundary follow-up parent review changed")
    plan = copy.deepcopy(original)
    for rid, pin in followup["reviewed_input_sha256"].items():
        if rid in plan["reviewed_input_sha256"] and plan["reviewed_input_sha256"][rid] != pin:
            raise ValueError("follow-up cannot silently replace a source version")
        plan["reviewed_input_sha256"][rid] = pin
    plan["claims"].extend(followup["claims"])
    plan["activities"].extend(followup["activities"])
    plan["mappings"].extend(followup["mappings"])
    for code, identity in followup["atlas_identities"].items():
        if code in plan["atlas_identities"] and plan["atlas_identities"][code] != identity:
            raise ValueError("follow-up cannot replace an existing Atlas identity")
        plan["atlas_identities"][code] = identity
    by_activity = {a["id"]: a for a in plan["activities"]}
    for change in followup["activity_followups"]:
        by_activity[change["activity_id"]]["candidate_source_bindings"] = change["candidate_source_bindings"]
    by_mapping = {m["id"]: m for m in plan["mappings"]}
    for change in followup["mapping_followups"]:
        mapping = by_mapping[change["mapping_id"]]
        mapping["history"] = [copy.deepcopy(mapping)]
        mapping.update(rationale=change["rationale"], claim_ids=mapping["claim_ids"] + change["claim_ids"],
                       boundary_status=change["status"])
    by_issue = {i["id"]: i for i in plan["new_issues"]}
    for change in followup["issue_followups"]:
        issue = by_issue[change["issue_id"]]
        issue["history"] = [copy.deepcopy(issue)]
        issue.update(status=change["status"], followup=change)
        issue["claim_ids"] = list(dict.fromkeys(issue["claim_ids"] + change["claim_ids"]))
    plan["directory_proposals"] = followup["directory_proposals"]
    plan["boundary_followup"] = {k: v for k, v in followup.items() if k != "claims"}
    return plan
