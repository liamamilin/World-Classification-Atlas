"""Bounded activity evidence, separate from the publisher's historical crosswalk."""
from collections import Counter
import re
from .acquire import sha256
from .registry import read_json, write_json
from .isic_review import ancestors, components


def field_value(document, path):
    value = document
    for key in path.split("."):
        value = value[key]
    if not isinstance(value, str):
        raise ValueError("evidence selector must reference a text field")
    return value


def resolve_claim(claim, documents):
    document = documents[claim["document"]]
    field = field_value(document, claim["field"])
    start, end = claim["start"], claim["end"]
    if not (0 <= start < end <= len(field)):
        raise ValueError(f"invalid evidence span: {claim['id']}")
    selected = field[start:end]
    if sha256(field.encode()) != claim["field_sha256"] or sha256(selected.encode()) != claim["text_sha256"]:
        raise ValueError(f"activity clause changed: {claim['id']}")
    if claim["role"] == "inclusion" and claim["field"] not in ("notes.inclusion", "notes.includes", "notes.includes_also"):
        raise ValueError("an exclusion or revision reason cannot masquerade as an inclusion")
    if claim["role"] == "exclusion_to_target":
        target = claim["target_node_id"].split(":")[-1]
        if claim["field"] not in ("notes.exclusion", "notes.excludes") or target not in re.findall(r"\b\d{4}\b", selected):
            raise ValueError("cross-reference does not name the claimed target class")
    return {**claim, "offset_unit": "unicode_codepoints_in_parsed_original_field",
            "evidence": document["evidence"]}, selected


def validate_activity(activity, claims):
    if activity["status"] not in ("accepted_bounded_activity", "accepted_current_activity"):
        raise ValueError("only explicitly accepted bounded activities enter the directory")
    for binding in activity["source_bindings"]:
        if not binding["node_id"].startswith(("ISIC:Rev.4:", "ISIC:Rev.5:")):
            raise ValueError("product evidence cannot become an activity source binding")
        if binding["relation"] != "broadMatch":
            raise ValueError("an activity slice cannot be promoted to whole source-class equivalence")
        refs = [claims[c] for c in binding["claim_ids"]]
        # An explicit inclusion is sufficient. A cross-reference allocation must actually
        # name this target class, and is marked separately from a target inclusion.
        if not any((c["document"] == binding["node_id"] and c["role"] == "inclusion")
                   or (c["role"] == "exclusion_to_target" and c.get("target_node_id") == binding["node_id"])
                   for c in refs):
            raise ValueError(f"activity binding lacks source inclusion/allocation evidence: {activity['key']}")
    if not any(b["node_id"] == "ISIC:Rev.5:" + activity["parent_rev5_code"] for b in activity["source_bindings"]):
        raise ValueError("activity parent must be a cited current source class")
    editions = {b["node_id"].split(":")[1] for b in activity["source_bindings"]}
    expected = {"Rev.5"} if activity["status"] == "accepted_current_activity" else {"Rev.4", "Rev.5"}
    if editions != expected:
        raise ValueError("activity edition claims differ from its reviewed status")


def validate_mapping(mapping, activities, official):
    pair = (mapping["from_code"], mapping["to_code"])
    if mapping["origin"] not in ("official_row_review", "atlas_research_supplement"):
        raise ValueError("unknown mapping authority")
    if (mapping["origin"] == "official_row_review") != (pair in official):
        raise ValueError("research supplement cannot masquerade as an official correspondence row")
    if mapping["status"] == "held_after_research":
        if mapping["relation"] is not None:
            raise ValueError("held mapping must not expose an approved relation")
        return
    if mapping["status"] != "accepted_scoped_overlap" or mapping["relation"] != "relatedMatch":
        raise ValueError("scoped activity evidence only approves a class association, never whole-class containment")
    if not mapping["activity_ids"]:
        raise ValueError("scope-limited mapping requires accepted activity evidence")
    for aid in mapping["activity_ids"]:
        bindings = {b["node_id"] for b in activities[aid]["source_bindings"]}
        if not {"ISIC:Rev.4:" + pair[0], "ISIC:Rev.5:" + pair[1]} <= bindings:
            raise ValueError("mapping activity evidence does not support both endpoints")
    edge = official.get(pair)
    if edge and (edge["publisher_uncertainty"] or edge["qualified_code_issues"]):
        raise ValueError("bounded evidence cannot remove a publisher question or identifier anomaly")


def research(root, old, new, errata, edges, pdf_documents, auxiliary_documents=None):
    plan = read_json(root / "data/research/isic-priority-review.json")
    from .isic_boundaries import extend_plan
    plan = extend_plan(root, plan)
    documents = {n["id"]: n for n in old + new}
    documents.update({"erratum:" + n["code"]: n for n in errata})
    documents.update({f"pdf:{rid}:{p['pdf_page']}": p for rid, pages in pdf_documents.items() for p in pages})
    documents.update(auxiliary_documents or {})
    observed = {d["evidence"]["resource_id"]: d["evidence"]["sha256"] for d in documents.values()}
    observed[edges[0]["evidence"]["resource_id"]] = edges[0]["evidence"]["sha256"]
    required_pins = {rows[0]["evidence"]["resource_id"] for rows in (old, new, edges)}
    required_pins.update(documents[c["document"]]["evidence"]["resource_id"] for c in plan["claims"])
    if not required_pins <= set(plan["reviewed_input_sha256"]):
        raise ValueError("priority review omits a cited source pin")
    if any(observed.get(rid) != pin for rid, pin in plan["reviewed_input_sha256"].items()):
        raise ValueError("priority research source bytes changed")
    claims, local_claims = {}, []
    for claim in plan["claims"]:
        if claim["id"] in claims:
            raise ValueError("duplicate activity claim ID")
        record, text = resolve_claim(claim, documents)
        claims[claim["id"]] = record
        local_claims.append({**record, "selected_source_text": text})
    activities = {a["id"]: a for a in plan["activities"]}
    if len(activities) != len(plan["activities"]):
        raise ValueError("duplicate bounded activity identity")
    for activity in activities.values():
        validate_activity(activity, claims)
        for binding in activity.get("candidate_source_bindings", []):
            if (binding["relation"] is not None or binding["node_id"] not in documents or not binding["claim_ids"]
                    or not binding["node_id"].startswith(("ISIC:Rev.4:", "ISIC:Rev.5:"))):
                raise ValueError("candidate source cannot expose an approved relation or lack evidence")
            if set(binding["claim_ids"]) - set(claims):
                raise ValueError("unknown candidate source evidence")
    official = {(e["from_code"], e["to_code"]): e for e in edges}
    mappings, seen = [], set()
    for mapping in plan["mappings"]:
        pair = (mapping["from_code"], mapping["to_code"])
        if pair in seen:
            raise ValueError("duplicate priority mapping pair")
        seen.add(pair)
        validate_mapping(mapping, activities, official)
        evidence_refs = set(mapping.get("claim_ids", []))
        for aid in mapping["activity_ids"]:
            evidence_refs.update(c for b in activities[aid]["source_bindings"] for c in b["claim_ids"])
        record = {**mapping, "allocation_weight": None, "scope_limit": "only the enumerated activities; no full-class allocation assertion",
                  "claim_evidence": [claims[c] for c in sorted(evidence_refs)],
                  "reviewer": plan["reviewer"], "reviewed_on": plan["reviewed_on"]}
        if pair in official:
            record["official_mapping_id"] = official[pair]["id"]
            record["evidence"] = official[pair]["evidence"]
        else:
            record["official_mapping_id"] = None
            record["evidence"] = record["claim_evidence"][0]["evidence"]
        mappings.append(record)
    # Review every historical companion row even when newly researched activities
    # create links between previously disconnected historical components.
    reviewed_pairs = {(m["from_code"], m["to_code"]) for m in mappings if m["origin"] == "official_row_review"}
    groups = [g for g in components(edges) if any((e["from_code"], e["to_code"]) in reviewed_pairs for e in g)]
    if {e["id"] for g in groups for e in g} != {official[p]["id"] for p in reviewed_pairs}:
        raise ValueError("priority review omitted historical companion rows")
    current = {n["code"]: n for n in new}
    anchors = {m["to_code"] for m in mappings if m["status"] == "accepted_scoped_overlap"}
    anchors.update(a["parent_rev5_code"] for a in activities.values())
    needed = anchors | {p for code in anchors for p in ancestors(current[code], current)}
    if set(plan["atlas_identities"]) != needed:
        raise ValueError("priority identity registry differs from reviewed anchors")
    issue_updates = {i["issue_id"]: i for i in plan["issue_followups"]}
    if len(issue_updates) != len(plan["issue_followups"]):
        raise ValueError("duplicate issue follow-up")
    for finding in plan["errata_findings"]:
        for cid in finding["claim_ids"]:
            if cid not in claims:
                raise ValueError("unknown errata evidence reference")
    if len({f["code"] for f in plan["errata_findings"]}) != len(plan["errata_findings"]):
        raise ValueError("duplicate focused erratum finding")
    for followup in plan["issue_followups"]:
        if set(followup["activity_ids"]) - set(activities):
            raise ValueError("issue follow-up cites an unknown activity")
    for issue in plan["new_issues"]:
        if not issue["claim_ids"] or set(issue["claim_ids"]) - set(claims):
            raise ValueError("new issue lacks valid clause evidence")
        issue["evidence"] = [claims[c]["evidence"] for c in issue["claim_ids"]]
    for proposal in plan.get("directory_proposals", []):
        if proposal["status"] != "held_after_research" or proposal.get("source_bindings"):
            raise ValueError("held directory proposal cannot expose approved source bindings")
        if not proposal["claim_ids"] or set(proposal["claim_ids"]) - set(claims):
            raise ValueError("directory proposal lacks valid evidence")
        if any(p not in documents or not p.startswith("ISIC:Rev.5:") for p in proposal["candidate_parent_source_ids"]):
            raise ValueError("proposal parent must be a current activity class")
    boundary = plan.get("boundary_followup")
    if boundary:
        write_json(root / "data/reports/isic-boundary-review.json", {**boundary,
                   "claims": [c for c in claims.values() if c["id"].startswith("B")],
                   "statistics": {"claims": sum(c.startswith("B") for c in claims),
                                  "new_activities": len(boundary["activities"]),
                                  "current_only_activities": sum(a["status"] == "accepted_current_activity" for a in boundary["activities"]),
                                  "official_row_reviews": len(boundary["mappings"]),
                                  "issue_followups": len(boundary["issue_followups"])}})
    public = {**{k: v for k, v in plan.items() if k != "claims"}, "claims": list(claims.values()), "mappings": mappings,
              "statistics": {"claims": len(claims), "bounded_activities": len(activities),
                             "activity_review_status": dict(Counter(a["status"] for a in activities.values())),
                             "official_rows_reviewed": len(reviewed_pairs), "complete_historical_components": len(groups),
                             "nontrivial_historical_components": sum(len(g) > 1 for g in groups),
                             "mapping_origin_status": dict(Counter(m["origin"] + ":" + m["status"] for m in mappings)),
                             "errata_findings": len(plan["errata_findings"]), "issue_followups": len(issue_updates)}}
    write_json(root / "data/reports/isic-priority-review.json", public)
    write_json(root / "data/local/economy/isic/priority-evidence-dossiers.json", {**public, "claims": local_claims})
    return public
