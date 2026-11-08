"""Source checks for bounded furniture material and historical scope decisions."""
import copy

from .acquire import sha256
from .furniture_followup import PLAN as PREVIOUS_PLAN, add_mapping_scopes, append_review_entries, update_issues
from .isic_boundaries import correspondence_rows
from .registry import read_json

PLAN = "data/research/furniture-material-boundary-review.json"
ASSETS = ("isic5-notes-20240311", "cpc21-manual-2015", "isic4-manual-2008", "isic5-white-cover-2026")
BASIS = "group_inclusion_and_material_class_scope"


def extend_plan(root, previous, observed):
    review = read_json(root / PLAN)
    if review["parent_review_sha256"] != sha256((root / PREVIOUS_PLAN).read_bytes()):
        raise ValueError("previous furniture review changed")
    pins = review["reviewed_input_sha256"]
    if not set(ASSETS) <= pins.keys() or any(observed[rid] != digest for rid, digest in pins.items()):
        raise ValueError("material boundary reviewed source bytes changed")
    result = copy.deepcopy(previous)
    append_review_entries(result, review)
    add_mapping_scopes(result, review)
    update_issues(result, review)
    activities = {a["id"]: a for a in result["activities"]}
    for update in review["activity_followups"]:
        activity = activities[update["activity_id"]]
        for child in update["child_activity_ids"]:
            if activity["id"] not in activities[child]["parents"]:
                raise ValueError("activity review references an unrelated child")
        activity.setdefault("scope_followups", []).append(update)
    official = {r["mapping_id"]: r for r in result["official_reviews"]}
    for update in review["official_review_followups"]:
        official[update["mapping_id"]].setdefault("scope_followups", []).append(update)
    result["material_boundary_review"] = {
        "review_sha256": sha256((root / PLAN).read_bytes()),
        "parent_review_sha256": review["parent_review_sha256"],
        "reviewed_input_sha256": pins,
        "reviewed_on": review["reviewed_on"],
    }
    return result, review


def note_revision_id(code):
    return f"ISIC:Rev.5:{code}@note-revision-2026"


def evidence_documents(pages, revisions, old):
    cpc = [{"pdf_page": p["evidence"]["pdf_page"], **p} for p in pages["cpc21-manual-2015"]]
    product, = correspondence_rows(cpc, {n["code"] for n in old}, selected={"38160"})
    if product["industry_code"] != "3100":
        raise ValueError("CPC principal industry reference changed")
    product.update(classification_object="products and services",
                   use="principal producing industry reference only; not activity allocation")
    revisions_by_id = {note_revision_id(e["code"]): e for e in revisions if e["code"] in ("2392", "2393")}
    documents = {**revisions_by_id}
    for rid, source in pages.items():
        for p in source:
            documents[f"{rid}:page:{p['evidence']['pdf_page']}"] = p
    return documents, product


def supports_material_slice(binding, claims, documents, activity, activities):
    """Approve only the reviewed material child, using its parent's explicit process."""
    key = binding["node_id"]
    materials = {"ISIC:Rev.5:3101": "wood_frame_or_frameless_predominantly_wood",
                 "ISIC:Rev.5:3102": "all_metal_furniture_with_metal_frame"}
    refs = [claims[c] for c in binding["claim_ids"]]
    parents = [activities[p] for p in activity["parents"] if p in activities]
    group = "ISIC:Rev.5:310"
    if (key not in materials or binding.get("material_scope") != materials[key]
            or binding.get("process_scope") != "integrated_finishing_of_new_household_furniture"
            or binding.get("source_level") != "class"
            or len(parents) != 1 or parents[0]["key"] != "new-furniture-surface-finishing"
            or documents[key]["parents"] != ["310"]):
        return False
    parent = parents[0]
    parent_group_claims = {cid for b in parent["source_bindings"] if b["node_id"] == group for cid in b["claim_ids"]}
    return (any(c["id"] in parent_group_claims and c["document"] == group
                and c["role"] == "inclusion" and c["field"] == "notes.includes_also" for c in refs)
            and any(c["document"] == key and c["role"] == "material_class_scope"
                    and c["field"] == "notes.includes" for c in refs))


def check_scoped_review(decision, edge, activities, claims):
    if not decision["activity_ids"] or not decision["claim_ids"] or any(c not in claims for c in decision["claim_ids"]):
        raise ValueError("material scope review missing evidence")
    expected = "relatedMatch" if decision["status"] == "reviewed_scoped_correspondence" else None
    if decision["status"] not in ("reviewed_scoped_correspondence", "held_for_this_activity") or decision["relation"] != expected:
        raise ValueError("material scope review cannot approve whole-class equivalence")
    for aid in decision["activity_ids"]:
        nodes = {b["node_id"] for b in activities[aid]["source_bindings"]}
        if decision["relation"] == "relatedMatch" and not {edge["from"], edge["to"]} <= nodes:
            raise ValueError("official review lacks a bounded activity shared by both endpoints")


def check_comparisons(comparisons, edges, assets, mappings, claims):
    """Check a scoped missing pair against each complete, pinned table."""
    results = []
    for comparison in comparisons:
        rid = comparison["resource_id"]
        table = [e for e in edges if e["evidence"]["resource_id"] == rid]
        pair = (comparison["absent_from"], comparison["absent_to"])
        if not table or any((e["from"], e["to"]) == pair for e in table):
            raise ValueError("expected absent official pair now present or table unavailable")
        adjacent = [e for e in table if e["from"] == pair[0] or e["to"] == pair[1]]
        if not adjacent or {e["id"] for e in adjacent} != set(comparison["expected_adjacent_mapping_ids"]):
            raise ValueError("official adjacency changed; material comparison must be reviewed")
        research = mappings[comparison["research_mapping_id"]]
        if {research["from"], research["to"]} != set(pair):
            raise ValueError("missing-pair comparison must reference the same research endpoints")
        if not comparison["claim_ids"] or any(c not in claims for c in comparison["claim_ids"]):
            raise ValueError("official omission comparison missing definition evidence")
        results.append({**comparison, "status": "absent_in_checked_table", "official_mapping_id": None,
                        "table_rows_checked": len(table), "evidence": assets[rid]["evidence"],
                        "adjacent_rows": [{k: e.get(k) for k in ("id", "from", "to", "topology",
                            "gsim_ids", "publisher_partial_flags", "publisher_predicate", "evidence")}
                            for e in adjacent]})
    return results
