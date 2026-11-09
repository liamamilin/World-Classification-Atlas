"""HS 2022 source catalogue built from the UNSD code workbook and WCO contents."""
import re
import subprocess

from .normalize import qa
from .xlsx import read_workbook

STRUCTURE = "hs2022-unsd-structure"
CONTENTS = "hs2022-wco-contents"
SHEET = "HS22"
AGGREGATES = {"TOTAL", "99", "9999", "999999"}


def display_code(code):
    return code[:4] + "." + code[4:] if len(code) == 6 and code.isdigit() else code


def pdf_pages(asset):
    text = subprocess.check_output(["pdftotext", "-layout", str(asset["path"]), "-"]).decode("utf-8")
    return [page.splitlines() for page in text.removesuffix("\f").split("\f")]


def wco_contents(asset):
    sections, chapters, reserved = [], {}, {}
    section = None
    for page, lines in enumerate(pdf_pages(asset), 1):
        for index, line in enumerate(lines):
            match = re.fullmatch(r"\s*SECTION ([IVX]+)\s*", line)
            if match:
                section = match[1]
                title = []
                for part in lines[index + 1:]:
                    if not part.strip():
                        break
                    title.append(part.strip())
                if not title:
                    raise ValueError(f"WCO section {section} has no title")
                sections.append({"code": section, "label": " ".join(title), "parents": [],
                                 "pdf_page": page, "pdf_line": index + 1, "level": "section"})
                continue
            chapter = re.match(r"^\s*(\d{1,2})\s+\S", line)
            if not chapter:
                continue
            code = chapter[1].zfill(2)
            if code in chapters or code in reserved or section is None:
                raise ValueError(f"unexpected WCO chapter {code}")
            if "(Reserved for " in line:
                reserved[code] = {"pdf_page": page, "pdf_line": index + 1}
            else:
                chapters[code] = {"section": section, "pdf_page": page, "pdf_line": index + 1}
    if len(sections) != 21 or set(reserved) != {"77", "98", "99"}:
        raise ValueError("unexpected WCO section or reserved chapter coverage")
    return sections, chapters, reserved


def catalogue(assets):
    workbook = assets[STRUCTURE]
    contents = assets[CONTENTS]
    nodes, chapter_locs, reserved = wco_contents(contents)
    rows = read_workbook(workbook["raw"])[SHEET]
    if list(rows[0]["cells"].values()) != [
        "Classification", "Code", "Description", "Parent Code", "Level", "IsBasicLevel"
    ]:
        raise ValueError("unexpected UNSD HS22 worksheet header")
    chapter_codes, statistical = set(), {}
    for row in rows[1:]:
        fields = row["cells"]
        code, label, parent = fields["B"], fields["C"], fields.get("D")
        level, leaf = fields["E"], fields["F"]
        if fields["A"] != "H6" or not label:
            raise ValueError(f"missing edition or title in HS22 row {row['row']}")
        if code in AGGREGATES:
            statistical[code] = {"source_row": row["row"], "source_parent": parent, "source_level": level}
            continue
        if not re.fullmatch(r"[0-9]{2}(?:[0-9]{2}){0,2}", code) or level != str(len(code)) or (
            parent != (code[:-2] or "TOTAL") or leaf != ("1" if len(code) == 6 else "0")
        ):
            raise ValueError(f"invalid source hierarchy in HS22 row {row['row']}: {code}")
        node = {
            "code": display_code(code), "label": label, "source_code": code, "source_parent": parent,
            "source_row": row["row"], "level": {"2": "chapter", "4": "heading", "6": "subheading"}[level],
            "parents": [display_code(parent)],
        }
        if level == "2":
            chapter_codes.add(code)
            loc = chapter_locs[code]
            node.update(parents=[loc["section"]], pdf_page=loc["pdf_page"], pdf_line=loc["pdf_line"])
        nodes.append(node)
    for node in nodes:
        node["id"] = "HS:2022:" + node["code"]
    quality = qa(nodes)
    if chapter_codes != set(chapter_locs) or set(statistical) != AGGREGATES or (
        len(rows) - 1 != len(nodes) - quality["roots"] + len(statistical)
    ) or any(quality[key] for key in ("duplicate_codes", "orphan_parents", "self_links", "cycles")):
        raise ValueError("HS22 catalogue has structural discrepancies")
    return {
        "nodes": nodes, "quality": quality, "source_rows": len(rows) - 1,
        "statistical_rows": statistical, "reserved_chapters": reserved,
        "workbook": {**workbook["evidence"], "sheet": SHEET}, "contents": contents["evidence"],
    }
