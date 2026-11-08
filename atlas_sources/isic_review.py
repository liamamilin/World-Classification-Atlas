"""Explicit evidence reviews; source candidates are never promoted by graph shape alone."""
import difflib
import json
import re
from collections import Counter, defaultdict
from .acquire import sha256
from .registry import read_json, write_json
from .normalize import qa


def digest(value):
    return sha256(json.dumps(value, ensure_ascii=False, sort_keys=True).encode())


def tokens(value):
    # A representation comparison, deliberately NOT an equivalence test.
    return re.findall(r"\w+", (value or "").lower())


def text_agreement(updated, current):
    a, b = tokens(updated), tokens(current)
    if a == b:
        return "same_word_sequence"
    if a and b == a + a:
        return "current_repeats_updated_twice"
    return "different_word_sequence"


def components(edges):
    adjacent = defaultdict(set)
    for e in edges:
        a, b = e["from"], e["to"]
        adjacent[a].add(b)
        adjacent[b].add(a)
    seen, result = set(), []
    for start in sorted(adjacent):
        if start in seen:
            continue
        todo, group = [start], set()
        while todo:
            node = todo.pop()
            if node in group:
                continue
            group.add(node)
            todo.extend(adjacent[node] - group)
        seen.update(group)
        result.append([e for e in edges if e["from"] in group])
    return result


def inverse(relation):
    return {"exactMatch": "exactMatch", "narrowMatch": "broadMatch",
            "broadMatch": "narrowMatch", "relatedMatch": "relatedMatch"}[relation]


def ancestors(node, by_code):
    result, todo = [], list(node["parents"])
    while todo:
        code = todo.pop()
        if code in result:
            raise ValueError("cycle or repeated ancestor in review spine")
        result.append(code)
        todo.extend(by_code[code]["parents"])
    return result


def scope_evidence(node):
    return {"node_id": node["id"], "evidence": node["evidence"],
            "scope_sha256": digest({k: node[k] for k in ("definition", "parents", "component")})}


def edge_fingerprint(edge, old, new):
    return digest({"row": edge["original_fields"], "from_scope": scope_evidence(old),
                   "to_scope": scope_evidence(new)})


def erratum_fingerprint(note, node):
    return digest({"original": note["original_note_2024"], "updated": note["updated_note_2026"],
                   "current": node["definition"], "evidence": note["evidence"]})


def audit_errata(notes, new, decisions):
    by_code = {n["code"]: n for n in new}
    choices = {d["code"]: d for d in decisions}
    if len(choices) != len(decisions) or set(choices) != {e["code"] for e in notes}:
        raise ValueError("errata review must enumerate every note exactly once")
    public, local = [], []
    for note in notes:
        code = note["code"]
        node, choice = by_code[code], choices[code]
        if choice["reviewed_fingerprint"] != erratum_fingerprint(note, node):
            raise ValueError(f"errata evidence changed: {code}")
        agreement = text_agreement(note["updated_note_2026"], node["definition"])
        effect = choice["effect"]
        if effect not in ("no_additional_scope_effect", "allocation_review_required"):
            raise ValueError(f"unknown errata decision: {code}")
        if agreement != "same_word_sequence" and effect == "no_additional_scope_effect":
            raise ValueError(f"conflicting current text cannot release mappings: {code}")
        record = {**choice, "text_agreement": agreement, "note_evidence": note["evidence"],
                  "current_evidence": node["evidence"], "current_scope_sha256": scope_evidence(node)["scope_sha256"],
                  "comparison_is_semantic_approval": False,
                  "affected_class_codes": sorted(n["code"] for n in new if len(n["code"]) == 4
                                                 and code in [n["code"]] + ancestors(n, by_code))}
        public.append(record)
        local.append({**record, "original_note_2024": note["original_note_2024"],
                      "updated_note_2026": note["updated_note_2026"], "current_definition": node["definition"],
                      "original_to_updated_diff": list(difflib.unified_diff(
                          (note["original_note_2024"] or "").splitlines(),
                          (note["updated_note_2026"] or "").splitlines(), lineterm="")),
                      "updated_to_current_diff": list(difflib.unified_diff(
                          (note["updated_note_2026"] or "").splitlines(),
                          (node["definition"] or "").splitlines(), lineterm=""))})
    return public, local


def check_relation(edge, relation, errata_by_code):
    if edge["publisher_uncertainty"] or edge["qualified_code_issues"]:
        raise ValueError("uncertain publisher statement or identifier cannot be approved")
    for code in edge["updated_notes_affected_codes"]:
        if errata_by_code[code]["effect"] != "no_additional_scope_effect":
            raise ValueError(f"unresolved 2026 ancestor/class boundary: {code}")
    historical = edge["historical_skos_candidate"]
    # Related is an explicit conservative review of overlap, not inferred containment.
    if relation not in (historical, "relatedMatch") or relation is None:
        raise ValueError("review claims stronger/different containment than official candidate")
    if relation == "exactMatch" and edge["topology"] != "one_to_one":
        raise ValueError("multiple correspondences cannot be collapsed into equivalence")


def review(root, edges, old, new, errata, previous, legacy_concepts):
    plan = read_json(root / "data/research/isic-expanded-review.json")
    observed = {x[0]["evidence"]["resource_id"]: x[0]["evidence"]["sha256"] for x in (edges, old, new)}
    if plan["reviewed_input_sha256"] != observed:
        raise ValueError("expanded review source bytes changed; renewed review required")
    old_by = {n["code"]: n for n in old}
    new_by = {n["code"]: n for n in new}
    note_reviews, local_notes = audit_errata(errata, new, plan["errata_reviews"])
    for record, dossier in zip(note_reviews, local_notes):
        # Explicit comparative citations, including the Readme-corrected Rev.4 scope.
        comparison = record.get("comparison_rev4_codes", [])
        record["comparison_scope_evidence"] = [scope_evidence(old_by[c]) for c in comparison]
        dossier["comparison_scope_evidence"] = record["comparison_scope_evidence"]
    note_by = {n["code"]: n for n in note_reviews}
    groups = components(edges)
    by_pair = {(e["from_code"], e["to_code"]): e for e in edges}
    decisions, cohorts = {}, []
    prior = {(c["from_code"], c["to_code"]): c for c in previous["cases"]}
    for cohort in plan["cohorts"]:
        selected = [by_pair[(d["from_code"], d["to_code"])] for d in cohort["edges"]]
        closed = next(g for g in groups if selected[0]["id"] in {e["id"] for e in g})
        if {e["id"] for e in selected} != {e["id"] for e in closed} or len(selected) != len(closed):
            raise ValueError(f"review omitted/duplicated connected correspondence: {cohort['id']}")
        for decision, edge in zip(cohort["edges"], selected):
            pair = (edge["from_code"], edge["to_code"])
            if pair in decisions:
                raise ValueError("duplicate expanded review pair")
            if decision["reviewed_fingerprint"] != edge_fingerprint(edge, old_by[pair[0]], new_by[pair[1]]):
                raise ValueError(f"reviewed scope or correspondence evidence changed: {pair}")
            relation = decision["relation"]
            if relation:
                check_relation(edge, relation, note_by)
            decisions[pair] = {**decision, "cohort_id": cohort["id"], "reviewer": plan["reviewer"],
                               "reviewed_on": plan["reviewed_on"], "cohort_rationale": cohort["rationale"],
                               "status": "reviewed_current_relation" if relation else "held_after_review"}
        cohorts.append({**{k: v for k, v in cohort.items() if k != "edges"},
                        "edge_count": len(selected), "rev4_codes": sorted({e["from_code"] for e in selected}),
                        "rev5_codes": sorted({e["to_code"] for e in selected}),
                        "current_approved_edges": sum(bool(d["relation"]) for d in cohort["edges"])})
    # Preserve the earlier three accepted IDs and decisions, and all earlier holds as history.
    for pair, prior_case in prior.items():
        if prior_case["decision"] == "accept_official_equivalence":
            edge = by_pair[pair]
            check_relation(edge, "exactMatch", note_by)
            decisions[pair] = {"from_code": pair[0], "to_code": pair[1], "relation": "exactMatch",
                               "status": "reviewed_current_relation", "rationale": prior_case["rationale"],
                               "cohort_id": "legacy-reviewed-exact", "reviewer": prior_case["reviewer"],
                               "reviewed_on": prior_case["reviewed_on"], "legacy_decision_id": prior_case["id"]}
        elif pair not in decisions:
            decisions[pair] = {"from_code": pair[0], "to_code": pair[1], "relation": None,
                               "status": "held_after_review", "rationale": prior_case["rationale"],
                               "cohort_id": "legacy-held", "reviewer": prior_case["reviewer"],
                               "reviewed_on": prior_case["reviewed_on"]}
    conflicts = plan["issues"]
    # Public subset: only individually reviewed pairs. Complete queue and text stay local.
    cases, queue, local_cases = [], [], []
    for edge in edges:
        pair = (edge["from_code"], edge["to_code"])
        decision = decisions.get(pair)
        issues = [i["id"] for i in conflicts if edge["from_code"] in i.get("rev4_codes", [])
                  or edge["to_code"] in i.get("rev5_codes", [])]
        blocking = [c for c in edge["updated_notes_affected_codes"]
                    if note_by[c]["effect"] != "no_additional_scope_effect"]
        record = {"mapping_id": edge["id"], "from_code": pair[0], "to_code": pair[1],
                  "status": decision["status"] if decision else "not_reviewed",
                  "reviewed_relation_rev4_to_rev5": decision["relation"] if decision else None,
                  "official_candidate": edge["historical_skos_candidate"], "source_status": edge["decision_status"],
                  "topology": edge["topology"], "gsim_ids": edge["gsim_ids"], "allocation_weight": None,
                  "unresolved_2026_codes": blocking, "issue_ids": issues, "evidence": edge["evidence"]}
        queue.append(record)
        if decision:
            case = {**record, "review": decision,
                    "scope_evidence": [scope_evidence(old_by[pair[0]]), scope_evidence(new_by[pair[1]])],
                    "errata_review_refs": ["ISIC5-2026-" + c for c in edge["updated_notes_affected_codes"]],
                    "previous_decision": prior.get(pair)}
            cases.append(case)
            local_cases.append({**case, "official_statement": edge, "rev4": old_by[pair[0]], "rev5": new_by[pair[1]]})
    identities = plan["atlas_identities"]
    approved = [c for c in cases if c["status"] == "reviewed_current_relation"]
    anchors = {c["to_code"] for c in approved}
    needed = anchors | {p for code in anchors for p in ancestors(new_by[code], new_by)}
    if set(identities) != needed or len(set(identities.values())) != len(identities):
        raise ValueError("Atlas identity registry differs from reviewed directory spine")
    for concept in legacy_concepts:
        target = next(b["node_id"].split(":")[-1] for b in concept["source_bindings"] if b["node_id"].startswith("ISIC:Rev.5:"))
        if identities[target] != concept["id"]:
            raise ValueError("previous Atlas identity changed")
    directory = []
    for code in sorted(needed):
        source = new_by[code]
        is_activity = code in anchors
        bindings = [{"node_id": source["id"], "relation": "exactMatch" if is_activity else None,
                     "role": "reviewed_scope_anchor" if is_activity else "navigation_spine_only",
                     "evidence": source["evidence"]}]
        for case in approved:
            if case["to_code"] == code:
                bindings.append({"node_id": "ISIC:Rev.4:" + case["from_code"],
                                 "relation": inverse(case["reviewed_relation_rev4_to_rev5"]),
                                 "role": "reviewed_mapping", "review_mapping_id": case["mapping_id"],
                                 "evidence": case["evidence"]})
        directory.append({"id": identities[code], "scheme_id": plan["scheme_id"],
                          "kind": "reviewed_activity" if is_activity else "source_derived_navigation",
                          "anchor_source_id": source["id"], "parents": [identities[p] for p in source["parents"]],
                          "parent_basis": "selected_Rev5_source_navigation_not_cross_edition_parent_equivalence",
                          "scope_basis": scope_evidence(source), "source_bindings": bindings,
                          "label": source["label"], "definition": source["definition"],
                          "scope_limit": "Rev5 anchored research subset; no claim of complete source coverage"})
    reverse = defaultdict(list)
    for node in directory:
        for binding in node["source_bindings"]:
            reverse[binding["node_id"]].append({"atlas_id": node["id"], "relation_atlas_to_source": binding["relation"],
                                                 "role": binding["role"]})
    directory_qa = qa([{"code": n["id"], "parents": n["parents"], "definition": n["definition"]} for n in directory])
    if any(directory_qa[k] for k in ("duplicate_codes", "orphan_parents", "self_links", "cycles")):
        raise ValueError("reviewed directory integrity failed")
    stats = {"connected_components": len(groups), "nontrivial_components": sum(len(g) > 1 for g in groups),
             "reviewed_cohorts": len(cohorts), "reviewed_cases": len(cases),
             "reviewed_nontrivial_components": sum(c["edge_count"] > 1 for c in cohorts),
             "mapping_status": dict(Counter(c["status"] for c in queue)),
             "reviewed_relations": dict(Counter(c["reviewed_relation_rev4_to_rev5"] for c in approved)),
             "reviewed_rev4_classes": len({c["from_code"] for c in approved}),
             "reviewed_rev5_classes": len(anchors), "directory_nodes": len(directory),
             "directory_kinds": dict(Counter(n["kind"] for n in directory)),
             "reviewed_source_bindings": sum(b["relation"] is not None for n in directory for b in n["source_bindings"]),
             "navigation_bindings": sum(b["relation"] is None for n in directory for b in n["source_bindings"]),
             "directory_integrity": directory_qa,
             "errata_effect": dict(Counter(e["effect"] for e in note_reviews)),
             "errata_text_agreement": dict(Counter(e["text_agreement"] for e in note_reviews)),
             "unresolved_issues": len(conflicts), "queue_rows": len(queue)}
    public_nodes = [{k: v for k, v in n.items() if k not in ("label", "definition")} for n in directory]
    public = {"scheme_id": plan["scheme_id"], "classification_object": "economic activities",
              "status": "reviewed_research_subset", "binding_direction": "Atlas to source",
              "concepts": public_nodes, "source_to_atlas": dict(reverse), "statistics": stats,
              "labels_and_definitions": "Resolved locally from pinned source snapshots; redistribution rights unresolved."}
    write_json(root / "data/atlas/economy/reviewed-directory-index.json", public)
    write_json(root / "data/reports/isic-expanded-review.json", {"statistics": stats, "cohorts": cohorts,
                                                               "cases": cases, "errata_reviews": note_reviews, "issues": conflicts})
    output = root / "data/local/economy/isic"
    write_json(output / "reviewed-directory.json", directory)
    write_json(output / "reviewed-source-to-atlas.json", dict(reverse))
    write_json(output / "mapping-review-queue.json", queue)
    write_json(output / "review-dossiers.json", local_cases)
    write_json(output / "errata-review-dossiers.json", local_notes)
    return {"statistics": stats, "directory": directory, "cases": cases, "queue": queue,
            "errata_reviews": note_reviews, "issues": conflicts}
