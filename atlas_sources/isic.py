"""ISIC source enrichment and evidence-preserving cross-version alignment research."""
import io
import json
import re
import shutil
import subprocess
import sys
import uuid
import zipfile
from importlib.metadata import version
from collections import Counter, defaultdict
from pathlib import Path
from .acquire import check_payload, sha256, snapshot_dir
from .normalize import qa, table_nodes
from .registry import read_json, write_json
from .xlsx import read_workbook
from .isic_review import review

NAMESPACE = uuid.UUID("b61f81d8-409b-4faf-8c02-62311fc6b833")
REQUIRED = ("isic4-structure", "isic5-structure", "isic4-database", "isic4-manual-2008",
            "isic5-notes-20260819", "isic5-white-cover-2026", "isic5-errata-2026",
            "isic4-isic5-correspondence", "isic4-isic5-technical-note-20241025")


def stable_id(kind, value):
    return f"urn:atlas:{kind}:" + str(uuid.uuid5(NAMESPACE, value))


def get_assets(root, resources):
    lock = read_json(root / "data/resources.lock.json")
    assets = {}
    for rid in REQUIRED:
        r = next(r for r in resources if r["id"] == rid)
        pin = lock[rid]
        path = snapshot_dir(root, r, pin["sha256"]) / r["filename"]
        raw = path.read_bytes()
        manifest = read_json(path.parent / "manifest.json")
        if (sha256(raw) != pin["sha256"] or any(pin[k] != r[k] for k in ("source_id", "edition", "url"))
                or manifest["sha256"] != pin["sha256"] or manifest["url"] != r["url"]):
            raise ValueError(f"raw provenance mismatch: {rid}")
        if r["rights"]["local_processing"] is not True:
            raise ValueError(f"local processing permission not confirmed: {rid}")
        check_payload(raw, r)
        assets[rid] = {"resource": r, "raw": raw, "path": path,
                       "evidence": {"resource_id": rid, "edition": r["edition"], "url": r["url"],
                                    "sha256": pin["sha256"], "publication_date": r["publication_date"]}}
    return assets


def records(table):
    lengths = {len(values) for values in table.values()}
    if len(lengths) != 1:
        raise ValueError("inconsistent Access column lengths")
    return [dict(zip(table, values)) for values in zip(*table.values())]


def read_rev4(asset, output):
    try:
        from access_parser import AccessParser
    except ImportError:
        raise ValueError("ISIC4 Access adapter needs: python3 -m pip install -r requirements-isic.txt --target data/local/deps")
    with zipfile.ZipFile(io.BytesIO(asset["raw"])) as z:
        members = set(z.namelist())
        if members != {"Readme.txt", "ISIC4_english.mdb"}:
            raise ValueError(f"unexpected ISIC4 database archive members: {sorted(members)}")
        readme = z.read("Readme.txt").decode("cp1252")
        mdb = output / "ISIC4_english.mdb"
        mdb.write_bytes(z.read("ISIC4_english.mdb"))
    db = AccessParser(str(mdb))
    structure = records(db.parse_table("tblStructure_ISICRev4"))
    titles = records(db.parse_table("tblTitles_English_ISICRev4"))
    if len({r["Code"] for r in structure}) != len(structure) or len({r["Code"] for r in titles}) != len(titles):
        raise ValueError("duplicate Access code")
    by_code = {r["Code"]: r for r in structure}
    if set(by_code) != {r["Code"] for r in titles}:
        raise ValueError("Access structure/title code mismatch")
    nodes = []
    for row in titles:
        code = row["Code"]
        s = by_code[code]
        parent = s[f"Level{s['CodeLevel']-1}"] if s["CodeLevel"] > 1 else None
        inclusion, exclusion = row["ExplanatoryNoteInclusion"], row["ExplanatoryNoteExclusion"]
        definition = "\n\n".join(v for v in (inclusion, exclusion) if v) or None
        nodes.append({"id": f"ISIC:Rev.4:{code}", "source_id": "ISIC", "edition": "Rev.4",
                      "component": "official_database_with_readme_corrections_through_2011-05-31",
                      "code": code, "label": row["Description"], "parents": [parent] if parent else [],
                      "parent_origin": "official_database_Level_fields", "definition": definition,
                      "definition_origin": "official_database" if definition else None,
                      "notes": {"inclusion": inclusion, "exclusion": exclusion},
                      "original_fields": {"structure": s, "title": row},
                      "evidence": {**asset["evidence"], "table": "tblTitles_English_ISICRev4", "key": code}})
    by_code = {n["code"]: n for n in nodes}
    checks = {
        "3830_exclusion_removes_metal_qualifier": ("secondary raw materials" in (by_code["3830"]["notes"]["exclusion"] or "")
                                                 and "secondary metal raw materials" not in (by_code["3830"]["notes"]["exclusion"] or "")),
        "1313_removes_silk_screen_printing": "silk-screen printing" not in by_code["1313"]["definition"],
        "1811_includes_direct_textile_printing": "printing directly onto textiles" in by_code["1811"]["definition"],
        "51_uses_repair_in_exclusion": "excludes the repair of aircraft" in by_code["51"]["definition"],
        "3315_factory_rebuilding_refers_3011": "factory rebuilding of ships, see 3011" in by_code["3315"]["definition"],
    }
    if not all(checks.values()):
        raise ValueError(f"ISIC4 Readme correction verification failed: {checks}")
    return nodes, {"readme": readme, "readme_sha256": sha256(readme.encode("utf-8")),
                   "mdb_sha256": sha256(mdb.read_bytes()), "structure": structure, "titles": titles,
                   "readme_correction_checks": checks,
                   "level_names": records(db.parse_table("tblLevelNames_English_ISICRev4"))}


def code_without_section(value):
    if not isinstance(value, str) or not re.fullmatch(r"[A-Z](?:\d{2,4})?", value):
        raise ValueError(f"invalid qualified ISIC code: {value!r}")
    return value[1:] or value


def read_rev5(asset):
    book = read_workbook(asset["raw"])
    rows = book["ISIC5"]
    expected = ["ISIC Rev 5 Code (with Section)", "ISIC Rev 5 Code", "ISIC Rev 5 Title",
                "ISIC Rev 5 Introductory Text", "ISIC Rev 5 Includes", "ISIC Rev 5 Includes Also", "ISIC Rev 5 Excludes"]
    if list(rows[0]["cells"].values()) != expected:
        raise ValueError("ISIC5 notes workbook header changed")
    nodes = []
    for row in rows[1:]:
        c = row["cells"]
        if not any(c.values()):
            continue
        code = code_without_section(c["A"])
        # Despite the B1 label, the publisher's B column contains PARENT codes.
        parent = code_without_section(c["B"]) if c.get("B") else None
        notes = {key: c.get(col) for key, col in (("introductory", "D"), ("includes", "E"),
                                                 ("includes_also", "F"), ("excludes", "G"))}
        definition = "\n\n".join(v for v in notes.values() if v) or None
        nodes.append({"id": f"ISIC:Rev.5:{code}", "source_id": "ISIC", "edition": "Rev.5",
                      "component": "explanatory_notes_2026-08-19", "code": code, "label": c["C"],
                      "parents": [parent] if parent else [], "parent_origin": "official_workbook_column_B_verified_against_structure",
                      "definition": definition, "definition_origin": "official_workbook" if definition else None,
                      "notes": notes, "original_fields": row,
                      "evidence": {**asset["evidence"], "sheet": "ISIC5", "row": row["row"], "range": f"A{row['row']}:G{row['row']}"}})
    return nodes, book


def parse_errata(book, evidence):
    rows = book["Notes"]
    header = next(r["row"] for r in rows if r["cells"].get("A") == "ISIC Rev.5 Code")
    results = []
    for row in rows:
        if row["row"] <= header or not row["cells"].get("A"):
            continue
        c = row["cells"]
        code = c["A"].strip()
        if not re.fullmatch(r"[A-Z]|\d{2,4}", code):
            raise ValueError(f"unrecognized errata code: {code!r}")
        results.append({"code": code, "original_note_2024": c.get("C"), "updated_note_2026": c.get("D"),
                        "reason": c.get("E"), "nature": c.get("F"), "original_fields": row,
                        "evidence": {**evidence, "sheet": "Notes", "row": row["row"]}})
    return results


def change_ids(value):
    if not value or not value.strip():
        return []
    parts = value.split(";")
    result = []
    for part in parts:
        match = re.match(r"\s*(RC\d(?:\.\d)?|VC\d|NC)\s*-", part, re.I)
        if not match:
            raise ValueError(f"unrecognized GSIM term: {part!r}")
        result.append(match[1].upper())
    return result


def derive_relation(from_degree, to_degree, changes, uncertain=False):
    if uncertain:
        return None
    if from_degree == 1 and to_degree == 1:
        return "exactMatch" if not any(c.startswith("RC") for c in changes) else None
    if from_degree > 1 and to_degree == 1:
        return "narrowMatch"  # FROM has a narrower match TO.
    if from_degree == 1 and to_degree > 1:
        return "broadMatch"   # FROM has a broader match TO.
    return "relatedMatch"


def parse_correspondence(asset, old_nodes, new_nodes, errata):
    book = read_workbook(asset["raw"])
    rows = book["ISIC4-5"]
    if rows[0]["cells"].get("G") != "Type of change in GSIM (blank means no change)":
        raise ValueError("correspondence GSIM header changed")
    old, new = {n["code"]: n for n in old_nodes}, {n["code"]: n for n in new_nodes}
    edges = []
    for row in rows[1:]:
        c = row["cells"]
        if not any(c.values()):
            continue
        a, b = c.get("B"), c.get("E")
        if not isinstance(a, str) or not re.fullmatch(r"\d{4}", a) or not isinstance(b, str) or not re.fullmatch(r"\d{4}", b):
            raise ValueError(f"invalid class identifiers at row {row['row']}")
        if a not in old or b not in new:
            raise ValueError(f"correspondence endpoint mismatch at row {row['row']}")
        qualified_issues = []
        for column, code, nodes in (("A", a, old), ("D", b, new)):
            ancestor = nodes[code]
            while ancestor["parents"]:
                ancestor = nodes[ancestor["parents"][0]]
            expected_qualified = ancestor["code"] + code
            if c[column] != expected_qualified:
                qualified_issues.append({"column": column, "raw": c[column], "expected_from_structure_and_numeric_column": expected_qualified,
                                         "resolution": "numeric endpoint retained; anomalous qualified string preserved; review required"})
        ids = change_ids(c.get("G"))
        if set(ids) - {"RC1", "RC2", "RC3.1", "RC3.2", "RC4.1", "RC4.2", "RC5", "VC1", "VC2", "NC"}:
            raise ValueError(f"unsupported GSIM IDs: {ids}")
        edges.append({"id": stable_id("mapping", f"ISIC4-5-2025-01-17:{a}:{b}"),
                      "from": old[a]["id"], "to": new[b]["id"], "from_code": a, "to_code": b,
                      "from_qualified_code": c["A"], "to_qualified_code": c["D"],
                      "gsim_raw": c.get("G"), "gsim_ids": ids, "change_description": c.get("H"),
                      "publisher_uncertainty": "?" in (c.get("G") or ""),
                      "qualified_code_issues": qualified_issues,
                      "original_fields": row, "evidence": {**asset["evidence"], "sheet": "ISIC4-5", "row": row["row"], "range": f"A{row['row']}:H{row['row']}"},
                      "basis": "official_correspondence_updated_2025-01-17_for_2024_adopted_notes",
                      "allocation_weight": None})
    if len({(e["from_code"], e["to_code"]) for e in edges}) != len(edges):
        raise ValueError("duplicate correspondence pair; raw evidence retained, review required")
    forward, reverse = defaultdict(set), defaultdict(set)
    for edge in edges:
        forward[edge["from_code"]].add(edge["to_code"])
        reverse[edge["to_code"]].add(edge["from_code"])
    if set(forward) != {n["code"] for n in old_nodes if len(n["code"]) == 4}:
        raise ValueError("Rev.4 class coverage is incomplete")
    if set(reverse) != {n["code"] for n in new_nodes if len(n["code"]) == 4}:
        raise ValueError("Rev.5 class coverage is incomplete")
    changed = {r["code"] for r in errata}
    for edge in edges:
        a, b = edge["from_code"], edge["to_code"]
        fd, td = len(forward[a]), len(reverse[b])
        edge.update(from_degree=fd, to_degree=td,
                    topology="one_to_one" if fd == td == 1 else "one_to_many" if td == 1 else "many_to_one" if fd == 1 else "many_to_many",
                    from_scope="whole" if fd == 1 else "partial", to_scope="whole" if td == 1 else "partial",
                    scope_derivation="inference_from_complete_official_class_correspondence_graph")
        historical = derive_relation(fd, td, edge["gsim_ids"], edge["publisher_uncertainty"])
        ancestors, cursor = [b], new[b]
        while cursor["parents"]:
            p = cursor["parents"][0]
            ancestors.append(p)
            cursor = new[p]
        edge["updated_notes_affected_codes"] = sorted(changed & set(ancestors))
        edge["historical_skos_candidate"] = historical
        edge["current_skos_candidate"] = None if edge["updated_notes_affected_codes"] or edge["qualified_code_issues"] else historical
        edge["decision_status"] = ("review_source_identifier" if edge["qualified_code_issues"] else
                                   "review_publisher_question" if edge["publisher_uncertainty"] else
                                   "review_2026_notes" if edge["updated_notes_affected_codes"] else
                                   "review_real_change" if any(x.startswith("RC") for x in edge["gsim_ids"]) else
                                   "official_scope_equivalence_candidate" if historical == "exactMatch" else
                                   "review_topology_without_gsim")
        edge["automatic_concept_merge"] = False
    return edges, book


def validate_enrichment(nodes, structure):
    by_code = {n["code"]: n for n in nodes}
    if set(by_code) != {n["code"] for n in structure}:
        raise ValueError("notes and structure code sets differ")
    differences = []
    for node in structure:
        rich = by_code[node["code"]]
        if node["parents"] != rich["parents"]:
            raise ValueError(f"source parent conflict: {node['code']}")
        if node["label"] != rich["label"]:
            differences.append(node["code"])
    report = qa(nodes)
    if report["duplicate_codes"] or report["orphan_parents"] or report["cycles"] or report["self_links"]:
        raise ValueError("enriched source node integrity failed")
    report["label_differences_from_structure"] = differences
    report["missing_note_codes"] = [n["code"] for n in nodes if not n["definition"]]
    return report


def write_jsonl(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8")


def curate(root, edges, old_nodes, new_nodes):
    decisions = read_json(root / "data/research/isic-review-decisions.json")
    reviewed_hashes = decisions["reviewed_input_sha256"]
    observed = {edges[0]["evidence"]["resource_id"]: edges[0]["evidence"]["sha256"],
                old_nodes[0]["evidence"]["resource_id"]: old_nodes[0]["evidence"]["sha256"],
                new_nodes[0]["evidence"]["resource_id"]: new_nodes[0]["evidence"]["sha256"]}
    if observed != reviewed_hashes:
        raise ValueError("reviewed source bytes changed; previous curation decisions require renewed evidence review")
    by_pair = {(e["from_code"], e["to_code"]): e for e in edges}
    old, new = {n["id"]: n for n in old_nodes}, {n["id"]: n for n in new_nodes}
    cases, concepts = [], []
    for decision in decisions["cases"]:
        edge = by_pair[(decision["from_code"], decision["to_code"])]
        if decision["decision"] == "accept_official_equivalence":
            if (edge["decision_status"] != "official_scope_equivalence_candidate"
                    or edge["current_skos_candidate"] != "exactMatch"):
                raise ValueError(f"review decision invalidated by source changes: {decision['id']}")
            target = new[edge["to"]]
            concepts.append({"id": decision["atlas_concept_id"], "scheme_id": decisions["scheme_id"],
                             "label": target["label"], "label_origin": "ISIC Rev.5 official source; local use only",
                             "definition_source_refs": [edge["from"], edge["to"]],
                             "source_bindings": [{"node_id": edge["from"], "relation": "exactMatch"},
                                                 {"node_id": edge["to"], "relation": "exactMatch"}],
                             "decision_id": decision["id"], "evidence": edge["evidence"],
                             "status": "source_evidence_reviewed_research_concept"})
        cases.append({**decision, "mapping_id": edge["id"], "gsim_ids": edge["gsim_ids"],
                      "topology": edge["topology"], "from_scope": edge["from_scope"], "to_scope": edge["to_scope"],
                      "historical_skos_candidate": edge["historical_skos_candidate"],
                      "current_skos_candidate": edge["current_skos_candidate"], "source_status": edge["decision_status"],
                      "publisher_uncertainty": edge["publisher_uncertainty"],
                      "qualified_code_issues": edge["qualified_code_issues"],
                      "updated_notes_affected_codes": edge["updated_notes_affected_codes"], "evidence": edge["evidence"]})
    if len({c["id"] for c in concepts}) != len(concepts):
        raise ValueError("duplicate Atlas concept ID")
    # Only selected code/GSIM facts, provenance and our own review decisions are public;
    # no publisher definitions, labels, change descriptions or complete source tables.
    public = {"scheme_id": decisions["scheme_id"], "status": decisions["status"], "scope": decisions["scope"],
              "reviewed_cases": len(cases), "reviewed_concepts": len(concepts), "cases": cases}
    return public, concepts


def run(root, resources):
    deps = root / "data/local/deps"
    if deps.exists():
        sys.path.insert(0, str(deps))
    output = root / "data/local/economy/isic"
    output.mkdir(parents=True, exist_ok=True)
    try:
        assets = get_assets(root, resources)
        if not shutil.which("pdftotext"):
            raise ValueError("Poppler pdftotext is required for manual/errata text capture")
        old, database = read_rev4(assets["isic4-database"], output)
        new, notes_book = read_rev5(assets["isic5-notes-20260819"])
        old_structure = table_nodes(assets["isic4-structure"]["raw"], assets["isic4-structure"]["resource"])
        new_structure = table_nodes(assets["isic5-structure"]["raw"], assets["isic5-structure"]["resource"])
        old_qa, new_qa = validate_enrichment(old, old_structure), validate_enrichment(new, new_structure)
        errata = parse_errata(notes_book, assets["isic5-notes-20260819"]["evidence"])
        if {r["code"] for r in errata} - {n["code"] for n in new}:
            raise ValueError("errata contains unknown codes")
        edges, crosswalk_book = parse_correspondence(assets["isic4-isic5-correspondence"], old, new, errata)
        reviewed, concepts = curate(root, edges, old, new)
        expanded = review(root, edges, old, new, errata, reviewed, concepts)
        # Full source text and complete derived correspondence stay local while redistribution is unresolved.
        write_jsonl(output / "rev4-nodes.jsonl", old)
        write_jsonl(output / "rev5-nodes-20260819.jsonl", new)
        write_jsonl(output / "correspondence-20250117.jsonl", edges)
        write_json(output / "rev4-database-tables.json", database)
        write_json(output / "rev5-source-workbook.json", notes_book)
        write_json(output / "correspondence-source-workbook.json", crosswalk_book)
        write_json(output / "rev5-note-revisions.json", errata)
        write_json(output / "reviewed-atlas-concepts.json", concepts)
        reverse_index = defaultdict(list)
        for concept in concepts:
            for binding in concept["source_bindings"]:
                reverse_index[binding["node_id"]].append(concept["id"])
        write_json(output / "source-to-atlas.json", dict(reverse_index))
        write_json(root / "data/reports/isic-reviewed-cases.json", reviewed)
        write_json(root / "data/atlas/economy/reviewed-concept-index.json",
                   {"scheme_id": reviewed["scheme_id"], "classification_object": "economic activities",
                    "status": "reviewed_research_subset_not_complete_catalogue",
                    "concepts": [{k: c[k] for k in ("id", "scheme_id", "source_bindings", "decision_id", "evidence", "status")} for c in concepts],
                    "source_to_atlas": dict(reverse_index),
                    "labels_and_definitions": "Resolved from local source snapshots; not republished while source rights remain unresolved."})
        template = (Path(__file__).parent / "economy_view.html").read_text(encoding="utf-8")
        payload = json.dumps({"old": old, "new": new, "edges": edges, "errata": errata, "concepts": concepts,
                              "review": expanded}, ensure_ascii=False).replace("<", "\\u003c")
        (output / "index.html").write_text(template.replace("__ECONOMY_DATA__", payload), encoding="utf-8")
        pdfs = []
        tool_version = subprocess.check_output(["pdftotext", "-v"], stderr=subprocess.STDOUT).decode().splitlines()[0]
        for rid, asset in assets.items():
            if asset["resource"]["format"] != "pdf":
                continue
            data = subprocess.check_output(["pdftotext", "-layout", str(asset["path"]), "-"])
            text = data.decode("utf-8")
            pages = text.split("\f")
            if pages[-1] == "":
                pages.pop()
            write_jsonl(output / (rid + "-pages.jsonl"),
                        [{"pdf_page": i, "text": page, "evidence": asset["evidence"]} for i, page in enumerate(pages, 1)])
            pdfs.append({"resource_id": rid, "pages": len(pages), "text_sha256": sha256(data), "extractor": tool_version})
        stats = {"status": "passed", "domain": "01-economy", "classification_object": "economic activities",
                 "inputs": [assets[k]["evidence"] for k in REQUIRED], "rev4": old_qa, "rev5": new_qa,
                 "correspondence": {"rows": len(edges), "unique_pairs": len({(e['from_code'], e['to_code']) for e in edges}),
                                    "rev4_classes": len({e["from_code"] for e in edges}), "rev5_classes": len({e["to_code"] for e in edges}),
                                    "topology": dict(Counter(e["topology"] for e in edges)),
                                    "gsim_ids": dict(Counter(x for e in edges for x in e["gsim_ids"])),
                                    "publisher_question_rows": [e["evidence"]["row"] for e in edges if e["publisher_uncertainty"]],
                                    "qualified_identifier_issue_rows": [e["evidence"]["row"] for e in edges if e["qualified_code_issues"]],
                                    "blank_gsim_with_multiple_correspondences": [e["evidence"]["row"] for e in edges if not e["gsim_ids"] and e["topology"] != "one_to_one"],
                                    "decision_status": dict(Counter(e["decision_status"] for e in edges))},
                 "rev5_errata_records": len(errata), "rev5_errata_codes": [r["code"] for r in errata],
                 "curation": {"reviewed_cases": reviewed["reviewed_cases"], "reviewed_concepts": len(concepts),
                              "source_bindings": len(reverse_index), "held_cases": sum(c["decision"] == "hold" for c in reviewed["cases"])},
                 "expanded_review": expanded["statistics"],
                 "rev4_readme_corrections": database["readme_correction_checks"],
                 "reproducibility": {"python": sys.version.split()[0],
                                     "packages": {p: version(p) for p in ("access-parser", "construct", "tabulate")},
                                     "parser_sha256": {p: sha256((Path(__file__).parent / p).read_bytes()) for p in ("isic.py", "isic_review.py", "xlsx.py", "normalize.py")},
                                     "review_decisions_sha256": sha256((root / "data/research/isic-review-decisions.json").read_bytes()),
                                     "expanded_review_sha256": sha256((root / "data/research/isic-expanded-review.json").read_bytes())},
                 "pdfs": pdfs, "outputs": {"local_directory": str(output.relative_to(root))},
                 "automatic_concept_merges": 0,
                 "limits": ["UN raw data and full derived notes/mappings are local-only pending redistribution rights.",
                            "Mapping GSIM is a 2025 historical statement; affected 2026 notes require review.",
                            "SKOS relations are directional research candidates, not approved concept merges.",
                            "No allocation weights or mappings above class level are invented."]}
        write_json(root / "data/reports/isic-economy.json", stats)
        print(json.dumps({k: stats[k] for k in ("status", "correspondence", "rev5_errata_records")}, ensure_ascii=False, indent=2))
        return 0
    except (OSError, ValueError, KeyError, StopIteration, subprocess.CalledProcessError) as error:
        write_json(root / "data/reports/isic-economy.json", {"status": "failed", "error": f"{type(error).__name__}: {error}"})
        print(f"ISIC research failed: {error}")
        return 1
