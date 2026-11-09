"""Insee NAF structure, selected notes and directional correspondence evidence."""
import copy
import re
import struct
from collections import Counter

from .acquire import sha256
from .furniture_contracts import PLAN as PREVIOUS_PLAN
from .furniture_materials import apply_review
from .isic import stable_id
from .registry import read_json
from .xlsx import read_workbook

PLAN = "data/research/furniture-naf-review.json"
OLD_STRUCTURE, OLD_NOTES, STRUCTURE, NOTES, FORWARD, REVERSE = ASSETS = (
    "naf-rev2-hierarchy", "naf-rev2-cpf21-notes-2020", "naf-2025-structure-202610",
    "naf-2025-notes-2025", "naf-rev2-to-2025-202610", "naf-2025-to-rev2-202610",
)
SOURCE = "FR_NAF"
LEVEL_PATTERNS = (r"[A-V]", r"[0-9]{2}", r"[0-9]{2}\.[0-9]", r"[0-9]{2}\.[0-9]{2}", r"[0-9]{2}\.[0-9]{2}[A-Z]")
NOTE_FIELDS = {"comprend": "includes", "comprend aussi": "includes_also",
               "comprend également": "includes_also", "ne comprend pas": "excludes"}


def node_id(edition, code):
    return f"{SOURCE}:{edition}:{code}"


def node(edition, code, level, parent, label, evidence, original):
    return {"id": node_id(edition, code), "source_id": SOURCE, "edition": edition, "code": code,
            "level": level, "parents": [parent] if parent else [], "label": label,
            "definition": None, "original_fields": original, "evidence": evidence}


def old_structure(asset):
    raw = asset["raw"]
    if len(raw) < 193 or raw[0] != 3:
        raise ValueError("unexpected NAF dBASE file format")
    count, start, width = struct.unpack_from("<IHH", raw, 4)
    fields = [(raw[i:i + 11].split(b"\0", 1)[0], raw[i + 11:i + 12], raw[i + 16])
              for i in range(32, 192, 32)]
    expected = [(f"NIV{i}".encode(), b"C", length) for i, length in zip(range(5, 0, -1), (6, 5, 4, 2, 1))]
    end = start + count * width
    if ((start, width) != (193, 19) or not count or end > len(raw) or fields != expected
            or raw[192:193] != b"\r" or raw[end:] not in (b"", b"\x1a")):
        raise ValueError("NAF dBASE hierarchy descriptors or record bounds changed")
    nodes = {}
    leaves = set()
    encoding = asset["resource"]["encoding"]
    for record in range(count):
        offset = start + record * width
        line = raw[offset:offset + width].decode(encoding)
        path = (line[18:19], line[16:18], line[12:16], line[7:12], line[1:7])
        if line[0] != " " or any(not re.fullmatch(p, c) for p, c in zip(LEVEL_PATTERNS, path)) or path[-1] in leaves:
            raise ValueError("invalid or duplicate NAF dBASE hierarchy record")
        leaves.add(path[-1])
        for i, code in enumerate(path):
            parent = path[i - 1] if i else None
            if code in nodes and nodes[code]["parents"] != ([parent] if parent else []):
                raise ValueError("NAF dBASE code has conflicting ancestors")
            if code not in nodes:
                nodes[code] = node("Rev.2", code, i + 1, parent, None,
                                   {**asset["evidence"], "record": record + 1, "byte_offset": offset},
                                   {f"NIV{j + 1}": c for j, c in enumerate(path)})
    return list(nodes.values())


def current_structure(asset):
    book = read_workbook(asset["raw"])
    sheet = "NAF 2025"
    rows = book[sheet]
    if rows[0]["cells"] != {"A": "NACE\nRev.2.1", "B": "NAF 2025\nsous-classes", "C": "Intitulés"}:
        raise ValueError("NAF 2025 structure workbook header changed")
    combined, parents = set(), {}
    section, parent_class = None, None
    for row in rows[1:]:
        cells = row["cells"]
        code, sub = cells.get("A"), cells.get("B")
        if code:
            combined.add(code)
            if re.fullmatch(LEVEL_PATTERNS[0], code):
                section = code
            if re.fullmatch(LEVEL_PATTERNS[1], code):
                parents[code] = section
            if re.fullmatch(LEVEL_PATTERNS[3], code):
                parent_class = code
        if sub:
            combined.add(sub)
            if parent_class != sub[:-1] or code and code != parent_class:
                raise ValueError("NAF subclass does not match published NACE class")
    nodes = []
    levels = ("Sections", "Divisions", "Groupes", "Classes", "Sous-classes")
    for i, level_sheet in enumerate(levels):
        for row in book[level_sheet][1:]:
            code, label = (row["cells"].get(k) for k in "AB")
            if not code and not label:
                continue
            if not code or not label or not re.fullmatch(LEVEL_PATTERNS[i], code):
                raise ValueError(f"invalid NAF code/title at {level_sheet}:{row['row']}")
            parent = (None, parents.get(code), code[:2], code[:4], code[:-1])[i]
            if i and not parent:
                raise ValueError("NAF division without published section")
            nodes.append(node("2025", code, i + 1, parent, label,
                              {**asset["evidence"], "sheet": level_sheet, "row": row["row"]}, row))
    if combined != {n["code"] for n in nodes}:
        raise ValueError("combined NAF structure and individual level sheets disagree")
    return nodes


def correspondence(asset, source, target, topology):
    (sheet, rows), = read_workbook(asset["raw"]).items()
    old_first = asset["resource"]["id"] == FORWARD
    a, b = ("NAF rév. 2", "NAF 2025") if old_first else ("NAF 2025", "NAF rév. 2")
    expected = [f"Sous-classes {a}\ncodes", f"Sous-classes {a}\n\nintitulés",
                "Contenu commun\ndes sous-classes en correspondance", f"Sous-classes {b}\ncodes",
                f"Sous-classes {b}\n\nintitulés", "Type de correspondance"]
    if [rows[0]["cells"].get(k) for k in "ABCDEF"] != expected:
        raise ValueError("NAF correspondence workbook header changed")
    start = {n["code"]: n["id"] for n in source if n["level"] == 5}
    end = {n["code"]: n["id"] for n in target if n["level"] == 5}
    edges = []
    for row in rows[1:]:
        cells = row["cells"]
        if not any(cells.values()):
            continue
        if any(v for k, v in cells.items() if k not in "ABCDEF"):
            raise ValueError("unexpected populated NAF correspondence column")
        x, y = cells.get("A"), cells.get("D")
        mapping_type = cells.get("F")
        if (not (x or y) or x and x not in start or y and y not in end
                or mapping_type not in ("Unique", "Multiple", None) or bool(x and y) != bool(mapping_type)):
            raise ValueError("invalid NAF correspondence endpoints or type")
        edges.append({"id": stable_id("mapping", f"{asset['resource']['id']}:{x}:{y}"),
                      "from": start.get(x), "to": end.get(y), "from_code": x, "to_code": y,
                      "from_label": cells.get("B"), "to_label": cells.get("E"),
                      "common_content": cells.get("C"), "publisher_mapping_type": mapping_type,
                      "original_fields": {k: cells.get(k) for k in "ABCDEF"},
                      "evidence": {**asset["evidence"], "sheet": sheet, "row": row["row"]}})
    if (len({(e["from"], e["to"]) for e in edges}) != len(edges)
            or {e["from_code"] for e in edges if e["from"]} != start.keys()
            or {e["to_code"] for e in edges if e["to"]} != end.keys()):
        raise ValueError("NAF correspondence duplicates or incomplete subclass coverage")
    topology(edges)
    for e in edges:
        if e["publisher_mapping_type"] and (e["publisher_mapping_type"] == "Unique") != (e["from_degree"] == 1):
            raise ValueError("NAF publisher mapping type disagrees with outgoing degree")
    return edges


def note_document(canonical, page, start, end, heading_evidence=None):
    text = page["text"]
    body = text[start:end]
    marker = re.compile(r"^\s*Cette sous-classe (comprend(?: aussi| également)?|ne comprend pas)\s*:", re.M)
    matches = list(marker.finditer(body))
    if not matches:
        raise ValueError(f"missing note markers for {canonical['id']}")
    notes = {}
    for i, m in enumerate(matches):
        limit = matches[i + 1].start() if i + 1 < len(matches) else len(body)
        notes[NOTE_FIELDS[m[1]]] = body[m.end():limit]
    evidence = {**page["evidence"], "page_start": start, "page_end": end}
    if heading_evidence:
        evidence["heading"] = heading_evidence
    return {**canonical, "id": f"{canonical['id']}@{page['evidence']['resource_id']}:p{evidence['pdf_page']}",
            "canonical_node_id": canonical["id"], "evidence": evidence,
            "notes": notes, "definition": body}


def selected_notes(pages, nodes, selections):
    """Cut reviewed PDF spans without reading interleaved product pages as activity notes."""
    components = []
    for s in selections:
        node_id_ = s["node_id"]
        canonical = nodes[node_id_]
        resource = OLD_NOTES if canonical["edition"] == "Rev.2" else NOTES
        page = pages[resource][s["page"] - 1]
        heading_page = pages[resource][s.get("heading_page", s["page"]) - 1]
        header = re.search(r"^ *" + re.escape(canonical["code"]) + r" +\S[^\n]+", heading_page["text"], re.M)
        if not header:
            raise ValueError(f"NAF note heading missing for {node_id_}")
        start = header.end() if page is heading_page and not s.get("continuation") else 0
        stop = re.search(s["end_pattern"], page["text"][start:], re.M)
        if not stop:
            raise ValueError(f"NAF note boundary missing for {node_id_}")
        component = note_document(canonical, page, start, start + stop.start(), heading_page["evidence"])
        component["label"] = canonical["label"] or header[0].strip().split(None, 1)[1]
        components.append(component)
    return components


def extend_plan(root, previous, observed):
    path = root / PLAN
    review = read_json(path)
    pins = review["reviewed_input_sha256"]
    if review["parent_review_sha256"] != sha256((root / PREVIOUS_PLAN).read_bytes()):
        raise ValueError("previous furniture contractor review changed")
    if not set(ASSETS) <= pins.keys() or any(observed[rid] != digest for rid, digest in pins.items()):
        raise ValueError("NAF boundary reviewed source bytes changed")
    result = apply_review(previous, review)
    activities = {a["id"]: a for a in result["activities"]}
    for addition in review["binding_additions"]:
        a = activities[addition["activity_id"]]
        used = {b["node_id"] for b in a["source_bindings"] + a.get("candidate_source_bindings", [])}
        for field in ("source_bindings", "candidate_source_bindings"):
            for binding in addition.get(field, []):
                key = binding["node_id"]
                if key in used or not key.startswith(SOURCE + ":"):
                    raise ValueError("NAF binding addition would replace existing evidence or add an unrelated source")
                a.setdefault(field, []).append(copy.deepcopy(binding))
                used.add(key)
    return result, review


def audit_correspondence(forward, reverse):
    opposite = {(e["to"], e["from"]): e for e in reverse}
    if {(e["from"], e["to"]) for e in forward} != opposite.keys():
        raise ValueError("NAF published directional code-pair sets disagree")
    return {"forward_rows": len(forward), "reverse_rows": len(reverse), "reversed_pair_sets_equal": True,
            "forward_types": dict(Counter(e["publisher_mapping_type"] or "blank" for e in forward)),
            "reverse_types": dict(Counter(e["publisher_mapping_type"] or "blank" for e in reverse)),
            "paired_common_content_text_differences": sum(e["common_content"] != opposite[(e["from"], e["to"])]["common_content"]
                                                          for e in forward)}


def read_sources(assets, review, pdf_pages, topology):
    old = old_structure(assets[OLD_STRUCTURE])
    current = current_structure(assets[STRUCTURE])
    forward = correspondence(assets[FORWARD], old, current, topology)
    reverse = correspondence(assets[REVERSE], current, old, topology)
    audit = audit_correspondence(forward, reverse)
    edges = forward + reverse
    nodes = {n["id"]: n for n in old + current}
    for edge in forward:
        if edge["from"] and edge["from_label"]:
            entry = nodes[edge["from"]]
            if entry["label"] is None:
                entry.update(label=edge["from_label"], label_evidence={**edge["evidence"], "column": "B"})
    pages = {rid: pdf_pages(assets[rid]) for rid in (OLD_NOTES, NOTES)}
    note_components = selected_notes(pages, nodes, review["note_selections"])
    for c in note_components:
        n = nodes[c["canonical_node_id"]]
        n["notes"] = c["notes"]
        n["definition"] = c["definition"]
        n["notes_evidence"] = c["evidence"]
    intro = pages[NOTES][1]
    statement = re.search(r"\b(\d+) sections\s+exemple", intro["text"])
    if not statement:
        raise ValueError("published NAF note count statement not found")
    measured = sum(n["level"] == 1 for n in current)
    audit["current_section_count_comparison"] = {"notes_reported": int(statement[1]), "structure_measured": measured,
                                                 "matches": int(statement[1]) == measured, "evidence": intro["evidence"]}
    return old, current, edges, note_components, pages, audit


def check_text_observations(specs, official):
    """Keep scoped common-content omissions separate from missing code pairs."""
    result = []
    for spec in specs:
        rows = [official[mid] for mid in spec["mapping_ids"]]
        if len(rows) != 2 or {r["evidence"]["resource_id"] for r in rows} != {FORWARD, REVERSE}:
            raise ValueError("NAF text observation requires each published direction")
        if (rows[0]["from"], rows[0]["to"]) != (rows[1]["to"], rows[1]["from"]):
            raise ValueError("NAF text observation endpoints do not reverse")
        found = [bool(re.search(spec["pattern"], r["common_content"] or "", re.I)) for r in rows]
        if any(match != spec["expected_mention"] for match in found):
            raise ValueError("NAF common-content observation changed")
        result.append({**spec, "directional_observations": [
            {**{k: r[k] for k in ("id", "from", "to", "evidence", "publisher_mapping_type")}, "mentioned": mentioned}
            for r, mentioned in zip(rows, found)]})
    return result
