"""Bounded same-object NACE/ISIC research, independent of the ISIC review history."""
import csv
import io
import json
import re
import shutil
import subprocess
import sys
import tempfile
from collections import Counter, defaultdict
from pathlib import Path

from .acquire import sha256, snapshot_dir
from .isic import (get_assets, read_rev4, read_rev5, parse_errata, parse_correspondence,
                   stable_id, write_jsonl)
from .isic_priority import resolve_claim
from .normalize import qa
from .registry import read_json, write_json
from .xlsx import read_workbook

NACE_ASSETS = ("nace21-download-list", "nace21-notes-20260930", "nace21-nace2-correspondence",
               "nace21-manual-2026", "nace2-manual-2008", "nace-reuse-policy",
               "isic4-nace2-correspondence", "isic4-nace2-change-history")
REQUIRED = NACE_ASSETS + ("isic4-database", "isic5-notes-20260819", "isic4-isic5-correspondence")
PLAN = "data/research/furniture-review.json"
BASE = "data/research/isic-expanded-review.json"
LOCAL = "data/local/economy/furniture"
PUBLIC = "data/atlas/economy/furniture-directory.json"
REPORT = "data/reports/furniture-alignment.json"
SCHEME = "urn:atlas:scheme:economic-activities-furniture-multisource"


def parent_code(code, section):
    if re.fullmatch(r"[A-Z]", code):
        return None
    if re.fullmatch(r"\d{2}", code):
        return section
    if re.fullmatch(r"\d{2}\.\d", code):
        return code[:2]
    if re.fullmatch(r"\d{2}\.\d{2}", code):
        return code[:-1]
    raise ValueError(f"invalid NACE code: {code}")


def checked_qa(nodes):
    result = qa(nodes)
    if any(result[k] for k in ("duplicate_codes", "orphan_parents", "self_links", "cycles")):
        raise ValueError(f"source/directory hierarchy invalid: {result}")
    return result


def nace_nodes(asset):
    book = read_workbook(asset["raw"])
    if set(book) != {"Sheet0"}:
        raise ValueError("NACE notes sheet changed")
    rows = book["Sheet0"]
    if list(rows[0]["cells"].values()) != ["ID", "Level", "Section", "Code", "Heading",
                "Implementation_Rule", "Includes", "Includes_also", "Excludes"]:
        raise ValueError("NACE notes header changed")
    nodes = []
    for row in rows[1:]:
        c = row["cells"]
        code = c["D"]
        parent = parent_code(code, c["C"])
        level = 1 if parent is None else 2 if len(code) == 2 else 3 if len(code) == 4 else 4
        if int(c["B"]) != level:
            raise ValueError("NACE code and level disagree")
        notes = {k: c.get(col) for k, col in (("implementation_rule", "F"), ("includes", "G"),
                                             ("includes_also", "H"), ("excludes", "I"))}
        nodes.append({"id": "NACE:Rev.2.1:" + code, "source_id": "NACE", "edition": "Rev.2.1",
                      "component": asset["evidence"]["resource_id"], "code": code, "level": level,
                      "publisher_id": c["A"], "label": c["E"], "parents": [parent] if parent else [],
                      "parent_origin": "derived_from_official_Section_Level_Code_fields",
                      "notes": notes, "definition": "\n\n".join(v for v in notes.values() if v) or None,
                      "original_fields": row, "evidence": {**asset["evidence"], "sheet": "Sheet0", "row": row["row"]}})
    checked_qa(nodes)
    return nodes


def pdf_pages(asset):
    raw = subprocess.check_output(["pdftotext", "-layout", str(asset["path"]), "-"])
    texts = raw.decode("utf-8").split("\f")
    if texts[-1] == "":
        texts.pop()
    return [{"text": text, "evidence": {**asset["evidence"], "pdf_page": i}}
            for i, text in enumerate(texts, 1)]


def nace2_selected(pages):
    # Only the bounded branch and its three incoming material classes, with ancestors.
    wanted = {"23", "23.4", "23.6", "23.7", "23.42", "23.69", "23.70",
              "31", "31.0", "31.01", "31.02", "31.03", "31.09"}
    result = []
    heading = re.compile(r"^[ \t]*(\d{2}(?:\.\d{1,2})?)[ \t]+([^\n]+)", re.M)
    for page in pages:
        # The appendix repeats the structure; it is not a second set of definitions.
        if not 100 <= page["evidence"]["pdf_page"] <= 300:
            continue
        text = page["text"]
        matches = list(heading.finditer(text))
        for i, match in enumerate(matches):
            code = match[1]
            if code not in wanted:
                continue
            end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
            body = text[match.end():end]
            includes, sep, excludes = body.partition("This class excludes:")
            parent = parent_code(code, "C")
            result.append({"id": "NACE:Rev.2:" + code, "source_id": "NACE", "edition": "Rev.2",
                           "code": code, "label": match[2].strip(), "parents": [parent],
                           "parent_origin": "manual_code_prefix_and_manufacturing_section",
                           "definition": body if body.strip() else None, "notes": {"includes": includes,
                           "excludes": sep + excludes if sep else ""},
                           "evidence": {**page["evidence"], "page_start": match.start(), "page_end": end}})
        if "Section C – Manufacturing" in text:
            result.append({"id": "NACE:Rev.2:C", "source_id": "NACE", "edition": "Rev.2", "code": "C",
                           "label": "Manufacturing", "parents": [], "definition": None, "notes": {},
                           "evidence": page["evidence"], "scope_limit": "heading only; section definition not extracted"})
    if {n["code"] for n in result} != wanted | {"C"}:
        raise ValueError("NACE2 selected manual coverage incomplete")
    checked_qa(result)
    return result


def topology(edges):
    outgoing, incoming = defaultdict(set), defaultdict(set)
    for e in edges:
        if e["to"] is not None:
            outgoing[e["from"]].add(e["to"])
            incoming[e["to"]].add(e["from"])
    for e in edges:
        a, b = len(outgoing[e["from"]]), len(incoming[e["to"]])
        e.update(from_degree=a, to_degree=b,
                 topology="no_correspondence" if e["to"] is None else ("one" if b == 1 else "many") + "_to_" + ("one" if a == 1 else "many"),
                 allocation_weight=None, relation=None, status="not_reviewed")
    return edges


def nace_correspondence(asset, nodes):
    rows = read_workbook(asset["raw"])["Sheet0"]
    if list(rows[0]["cells"].values()) != ["NACE21_Code", "LEVEL", "NACE21_Heading", "NACE2_Code",
            "NACE2_Heading", "Common_Content", "NumberOfCorresponding_NACE2", "TypeOfMapping", "TypeOfCorrespondence"]:
        raise ValueError("NACE correspondence header changed")
    known = {n["code"]: n for n in nodes}
    edges = []
    for row in rows[1:]:
        c = row["cells"]
        if c["A"] not in known or known[c["A"]]["level"] != int(c["B"]):
            raise ValueError("NACE correspondence current endpoint/level invalid")
        if c.get("D"):
            parent_code(c["D"], "C")  # syntax, not a fabricated old section allocation
        edges.append({"id": stable_id("mapping", "NACE21-NACE2:" + c["A"] + ":" + c["D"]),
                      "from": "NACE:Rev.2.1:" + c["A"], "to": "NACE:Rev.2:" + c["D"] if c.get("D") else None,
                      "level": int(c["B"]), "common_content": c.get("F"),
                      "publisher_correspondence_count": int(c["G"]), "publisher_mapping_type": c.get("H"),
                      "publisher_correspondence_type": c.get("I"), "original_fields": row,
                      "evidence": {**asset["evidence"], "sheet": "Sheet0", "row": row["row"]}})
    if len({(e["from"], e["to"]) for e in edges}) != len(edges):
        raise ValueError("duplicate NACE correspondence pair")
    topology(edges)
    if any(e["from_degree"] != e["publisher_correspondence_count"] for e in edges):
        raise ValueError("NACE publisher count disagrees with full correspondence graph")
    return edges


def isic_nace_correspondence(asset, old):
    reader = csv.DictReader(io.StringIO(asset["raw"].decode("utf-8")))
    if reader.fieldnames != ["ISIC4code", "ISIC4part", "NACE2code", "NACE2part"]:
        raise ValueError("ISIC-NACE header changed")
    known = {n["code"] for n in old}
    edges = []
    for line, row in enumerate(reader, 2):
        if row["ISIC4code"] not in known or any(row[k] not in ("0", "1") for k in ("ISIC4part", "NACE2part")):
            raise ValueError("ISIC-NACE endpoint/partial flag invalid")
        parent_code(row["NACE2code"], "C")
        edges.append({"id": stable_id("mapping", "ISIC4-NACE2:" + row["ISIC4code"] + ":" + row["NACE2code"]),
                      "from": "ISIC:Rev.4:" + row["ISIC4code"], "to": "NACE:Rev.2:" + row["NACE2code"],
                      "publisher_partial_flags": {"ISIC4part": row["ISIC4part"], "NACE2part": row["NACE2part"]},
                      "original_fields": row, "evidence": {**asset["evidence"], "line": line}})
    if len({(e["from"], e["to"]) for e in edges}) != len(edges):
        raise ValueError("duplicate ISIC-NACE pair")
    return topology(edges)


def extract(root, resources):
    assets = get_assets(root, resources, REQUIRED)
    output = root / LOCAL
    output.mkdir(parents=True, exist_ok=True)
    deps = root / "data/local/deps"
    # In a clean reconstruction the installed dependency location belongs to the original checkout.
    if deps.exists() and str(deps) not in sys.path:
        sys.path.insert(0, str(deps))
    old, _ = read_rev4(assets["isic4-database"], output)
    new, book = read_rev5(assets["isic5-notes-20260819"])
    errata = parse_errata(book, assets["isic5-notes-20260819"]["evidence"])
    isic_edges, _ = parse_correspondence(assets["isic4-isic5-correspondence"], old, new, errata)
    current = nace_nodes(assets["nace21-notes-20260930"])
    pdfs = {rid: pdf_pages(assets[rid]) for rid in ("nace2-manual-2008", "nace21-manual-2026")}
    previous = nace2_selected(pdfs["nace2-manual-2008"])
    cross = nace_correspondence(assets["nace21-nace2-correspondence"], current)
    legacy = isic_nace_correspondence(assets["isic4-nace2-correspondence"], old)
    return assets, old, new, current, previous, pdfs, cross, legacy, isic_edges, errata


def validate_slice(activity, claims, documents):
    if activity["status"] != "reviewed_bounded_activity":
        raise ValueError("unreviewed activity cannot enter directory")
    keys = set()
    for binding in activity["source_bindings"]:
        key = binding["node_id"]
        if key not in documents or documents[key]["source_id"] not in ("ISIC", "NACE"):
            raise ValueError("same-object activity source required")
        if key in keys or binding["relation"] != "broadMatch":
            raise ValueError("activity binding must be unique and point to a broader source class")
        keys.add(key)
        if not any(claims[c]["document"] == key and claims[c]["role"] == "inclusion" for c in binding["claim_ids"]):
            raise ValueError("activity binding lacks direct source inclusion evidence")
    if not {"ISIC:Rev.4", "ISIC:Rev.5", "NACE:Rev.2.1"} <= {k.rsplit(":", 1)[0] for k in keys}:
        raise ValueError("bounded multisource activity needs both ISIC editions and current NACE")
    for candidate in activity.get("candidate_source_bindings", []):
        if candidate["relation"] is not None or candidate["node_id"] in keys or candidate["node_id"] not in documents:
            raise ValueError("pending binding cannot become approved")


def validate_research_mapping(mapping, activities):
    if mapping["origin"] != "atlas_research" or mapping["official_mapping_id"] is not None or mapping["relation"] != "relatedMatch":
        raise ValueError("Atlas research cannot masquerade as official or whole-class equivalence")
    for aid in mapping["activity_ids"]:
        endpoints = {b["node_id"] for b in activities[aid]["source_bindings"]}
        if not {mapping["from"], mapping["to"]} <= endpoints:
            raise ValueError("research mapping needs shared activity at both endpoints")
    if not mapping["activity_ids"]:
        raise ValueError("research mapping requires bounded activity")


def build(root, resources):
    assets, old, new, current, previous, pdfs, cross, legacy, isic_edges, errata = extract(root, resources)
    plan = read_json(root / PLAN)
    observed = {rid: asset["evidence"]["sha256"] for rid, asset in assets.items()}
    if plan["reviewed_input_sha256"] != observed or plan["base_identity_registry_sha256"] != sha256((root / BASE).read_bytes()):
        raise ValueError("reviewed input/identity registry changed; review must be renewed")
    documents = {n["id"]: n for n in old + new + current + previous}
    documents.update({f"{rid}:page:{p['evidence']['pdf_page']}": p for rid, pages in pdfs.items() for p in pages})
    documents.update({e["id"]: e for e in cross + legacy})
    claims, dossiers = {}, []
    for claim in plan["claims"]:
        if claim["id"] in claims:
            raise ValueError("duplicate evidence ID")
        resolved, selected = resolve_claim(claim, documents)
        claims[claim["id"]] = resolved
        dossiers.append({**resolved, "selected_text": selected})
    activities = {a["id"]: a for a in plan["activities"]}
    if len(activities) != len(plan["activities"]):
        raise ValueError("duplicate activity ID")
    for activity in activities.values():
        validate_slice(activity, claims, documents)
    official = {e["id"]: e for e in cross + legacy}
    reviewed = []
    for decision in plan["official_reviews"]:
        edge = official[decision["mapping_id"]]
        if decision["relation"] not in (None, "relatedMatch") or (decision["status"].startswith("held") and decision["relation"] is not None):
            raise ValueError("branch review cannot upgrade correspondence to whole-class equivalence")
        if not decision["claim_ids"] or any(c not in claims for c in decision["claim_ids"]):
            raise ValueError("official row review missing evidence")
        reviewed.append({"mapping_id": edge["id"], "from": edge["from"], "to": edge["to"],
                         "evidence": edge["evidence"], "topology": edge["topology"],
                         "publisher_partial_flags": edge.get("publisher_partial_flags"), "review": decision})
    branch_edges = [e for e in cross if e["from"] == "NACE:Rev.2.1:31.00"]
    if {e["id"] for e in branch_edges} - {e["mapping_id"] for e in reviewed}:
        raise ValueError("incoming NACE furniture rows missing individual review")
    mappings = []
    for mapping in plan["research_mappings"]:
        validate_research_mapping(mapping, activities)
        mappings.append(mapping)
    ids = read_json(root / BASE)["atlas_identities"]
    nodes = plan["navigation"] + plan["anchors"] + plan["activities"]
    for node in plan["anchors"]:
        if node["id"] != ids[node["base_rev5_code"]]:
            raise ValueError("existing Atlas identity replaced")
        if any(b["relation"] not in ("relatedMatch", None) for b in node["additional_source_bindings"]):
            raise ValueError("partial anchor alignment cannot upgrade to whole-class equivalence")
    directory_qa = checked_qa([{**n, "code": n["id"], "definition": n.get("atlas_scope")} for n in nodes])
    reverse, candidates = defaultdict(list), defaultdict(list)
    for n in nodes:
        for b in n.get("source_bindings", []) + n.get("additional_source_bindings", []):
            reverse[b["node_id"]].append({"atlas_id": n["id"], "relation_atlas_to_source": b["relation"]})
        for b in n.get("candidate_source_bindings", []):
            candidates[b["node_id"]].append({"atlas_id": n["id"], "relation": None, "status": b["status"]})
    directory = {"scheme_id": SCHEME, "classification_object": "economic activities", "status": "bounded_multisource_research",
                 "binding_direction": "Atlas to source", "hierarchy_scope": "parents apply only in this scheme; original source and base directory paths retained independently",
                 "concepts": nodes, "source_to_atlas": dict(reverse), "source_to_candidates": dict(candidates),
                 "claims": list(claims.values()), "issues": plan["issues"], "research_mappings": mappings,
                 "official_reviews": reviewed}
    local = root / LOCAL
    write_json(root / PUBLIC, directory)
    for filename, value in (("nace21-nodes.jsonl", current), ("nace2-selected-nodes.jsonl", previous),
                            ("nace21-nace2-correspondence.jsonl", cross), ("isic4-nace2-correspondence.jsonl", legacy)):
        write_jsonl(local / filename, value)
    # EU text is reusable with attribution; UNSD original definitions remain local.
    write_jsonl(root / "data/normalized/NACE/Rev.2.1/notes-20260930.jsonl", current)
    write_jsonl(root / "data/normalized/NACE/Rev.2.1/correspondence-to-Rev.2.jsonl", cross)
    write_json(local / "evidence-dossiers.json", dossiers)
    source_nodes = {n["id"]: n for n in old + new + current + previous}
    wanted = {b["node_id"] for n in nodes for b in n.get("source_bindings", []) + n.get("candidate_source_bindings", []) + n.get("additional_source_bindings", [])}
    wanted.update("NACE:Rev.2:" + c for c in ("31.01", "31.02", "31.03", "31.09"))
    pending = list(wanted)
    while pending:
        key = pending.pop()
        node = source_nodes[key]
        for code in node["parents"]:
            parent = key.rsplit(":", 1)[0] + ":" + code
            if parent not in wanted:
                wanted.add(parent)
                pending.append(parent)
    branch_nodes = [n for key, n in source_nodes.items() if key in wanted]
    write_json(local / "source-branches.json", branch_nodes)
    for rid, pages in pdfs.items():
        write_jsonl(local / (rid + "-pages.jsonl"), pages)
    isic_branch = [e for e in isic_edges if e["from_code"] == "3100"]
    write_json(local / "isic-furniture-official-rows.json", isic_branch)
    stats = {"status": "passed", "inputs": list(asset["evidence"] for asset in assets.values()),
             "nace21": checked_qa(current), "nace2_selected": checked_qa(previous),
             "nace21_class_definitions": sum(bool(n["definition"]) for n in current if n["level"] == 4),
             "branch_source_nodes": dict(Counter(n["source_id"] + ":" + n["edition"] for n in branch_nodes)),
             "pdf_pages": {rid: len(pages) for rid, pages in pdfs.items()},
             "official_tables": {"nace21_to_nace2_rows": len(cross), "nace_levels": dict(Counter(e["level"] for e in cross)),
                                 "isic4_to_nace2_rows": len(legacy), "furniture_current_incoming_rows": len(branch_edges),
                                 "individually_reviewed_rows": len(reviewed)},
             "furniture_leaves": {"NACE:Rev.2.1": ["31.00"], "NACE:Rev.2": ["31.01", "31.02", "31.03", "31.09"],
                                   "ISIC:Rev.4": ["3100"], "ISIC:Rev.5": ["3101", "3102"]},
             "directory": directory_qa, "reused_ids": len(plan["anchors"]), "new_ids": len(nodes) - len(plan["anchors"]),
             "bounded_activities": len(activities), "approved_bindings": sum(len(v) for v in reverse.values()),
             "candidate_bindings": sum(len(v) for v in candidates.values()), "evidence_claims": len(claims),
             "research_mappings": len(mappings), "issues": plan["issues"],
             "isic_furniture_official_rows": [{k: e[k] for k in ("from_code", "to_code", "topology", "gsim_ids", "evidence")} for e in isic_branch],
             "affected_isic_furniture_2026_notes": [e["code"] for e in errata if e["code"] in ("C", "31", "310", "3100", "3101", "3102")],
             "affected_isic_material_2026_notes": [e["code"] for e in errata if e["code"] in ("C", "23", "239", "2393", "2395", "2396")],
             "reproducibility": {"python": sys.version.split()[0], "pdftotext": subprocess.check_output(["pdftotext", "-v"], stderr=subprocess.STDOUT).decode().splitlines()[0],
                                 "review_sha256": sha256((root / PLAN).read_bytes()), "base_identity_sha256": sha256((root / BASE).read_bytes()),
                                 "parser_sha256": {p: sha256((Path(__file__).parent / p).read_bytes()) for p in ("furniture.py", "furniture_view.html", "isic.py", "isic_priority.py", "xlsx.py", "normalize.py")}},
             "limits": ["No direct official NACE2.1-ISIC5 crosswalk found at checked endpoints; research edges are not transitive official edges.",
                        "Every furniture leaf has scoped research coverage; complete class equivalence remains unapproved.",
                        "NACE2 extraction is selected, not a full old scheme; no real-world entities or allocation weights."]}
    write_json(root / REPORT, stats)
    template = (Path(__file__).parent / "furniture_view.html").read_text()
    payload = {"directory": directory, "sources": read_json(local / "source-branches.json"),
               "evidence": dossiers, "official": reviewed, "stats": stats}
    (local / "index.html").write_text(template.replace("__FURNITURE_DATA__", json.dumps(payload, ensure_ascii=False).replace("<", "\\u003c")), encoding="utf-8")
    return stats


def run(root, resources):
    try:
        stats = build(root, resources)
        print(f"Furniture: {stats['nace21']['node_count']} NACE nodes; {stats['official_tables']['individually_reviewed_rows']} official rows reviewed; {stats['directory']['node_count']} branch nodes")
        return 0
    except (OSError, ValueError, KeyError, StopIteration, subprocess.CalledProcessError) as error:
        write_json(root / REPORT, {"status": "failed", "error": f"{type(error).__name__}: {error}"})
        print(f"Furniture research failed: {error}")
        return 1


def reproduce(root, resources):
    result = {"status": "failed", "method": "fresh directory; pinned raw assets, manifests and two research inputs only; no network", "files": []}
    try:
        if run(root, resources):
            raise ValueError("baseline failed")
        assets = get_assets(root, resources, REQUIRED)
        with tempfile.TemporaryDirectory(prefix="atlas-furniture-repro-") as folder:
            target = Path(folder)
            for rel in (PLAN, BASE, "data/resources.lock.json"):
                path = target / rel
                path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(root / rel, path)
            for asset in assets.values():
                dest = snapshot_dir(target, asset["resource"], asset["evidence"]["sha256"])
                dest.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(asset["path"], dest / asset["path"].name)
                shutil.copyfile(asset["path"].parent / "manifest.json", dest / "manifest.json")
            if run(target, resources):
                raise ValueError("clean rebuild failed")
            paths = [p.relative_to(target) for p in (target / LOCAL).rglob("*") if p.is_file()]
            paths += [Path(PUBLIC), Path(REPORT), Path("data/normalized/NACE/Rev.2.1/notes-20260930.jsonl"), Path("data/normalized/NACE/Rev.2.1/correspondence-to-Rev.2.jsonl")]
            for rel in sorted(paths):
                a, b = sha256((root / rel).read_bytes()), sha256((target / rel).read_bytes())
                result["files"].append({"path": str(rel), "sha256": b, "identical": a == b})
            result.update(status="passed" if all(f["identical"] for f in result["files"]) else "failed",
                          compared_files=len(paths), identical_files=sum(f["identical"] for f in result["files"]))
    except (OSError, ValueError, KeyError) as error:
        result["error"] = f"{type(error).__name__}: {error}"
    write_json(root / "data/reports/furniture-reproduction.json", result)
    print(f"Furniture clean reconstruction: {result['status']}; {result.get('identical_files', 0)}/{result.get('compared_files', 0)}")
    return int(result["status"] != "passed")
