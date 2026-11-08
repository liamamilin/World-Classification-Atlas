"""Official RDF evidence and append-only furniture review follow-ups."""
import copy
import json
import re
from collections import Counter, defaultdict
from urllib.parse import parse_qs, urlsplit

from .acquire import sha256
from .isic import stable_id
from .normalize import qa
from .registry import read_json
from .xlsx import read_workbook

PLAN = "data/research/furniture-followup-review.json"
ASSETS = ("nace2-download-list-20261109", "nace2-nace21-correspondence-20260831",
          "nace-showvoc-catalog-20261109", "nace2-cellar-selected-notes-20261109",
          "nace2-cellar-isic4-predicates-20261109", "nace-cellar-correspondence-schemes-20261109",
          "nace-cellar-current-mapping-targets-20261109", "nace-cellar-current-positive-control-20261109",
          "nace-cellar-nace2-isic4-xkos-20261109", "nace-cellar-current-incoming-isic-20261109")
SKOS = "http://www.w3.org/2004/02/skos/core#"
XKOS = "http://rdf-vocabulary.ddialliance.org/xkos#"
RDF_TYPE = "http://www.w3.org/1999/02/22-rdf-syntax-ns#type"
NACE2 = "http://data.europa.eu/ux2/nace2/"
CURRENT = "http://data.europa.eu/ux2/nace2.1/nace2.1"
UN4 = "https://unstats.un.org/classifications/ISIC/rev4/"
MAPPINGS = {SKOS + r for r in ("exactMatch", "closeMatch", "narrowMatch", "broadMatch", "relatedMatch")}


def result_rows(asset, variables):
    value = json.loads(asset["raw"])
    if value.get("head", {}).get("vars") != variables or not isinstance(value.get("results", {}).get("bindings"), list):
        raise ValueError("unexpected SPARQL result schema")
    rows = value["results"]["bindings"]
    for row in rows:
        if set(row) != set(variables) or any(not isinstance(v.get("value"), str) or v.get("type") not in ("uri", "literal", "typed-literal") for v in row.values()):
            raise ValueError("unbound or invalid SPARQL term")
    return rows


def check_queries(root, assets):
    for asset in assets.values():
        r = asset["resource"]
        if not r.get("query_file"):
            continue
        raw = (root / r["query_file"]).read_bytes()
        query = raw.decode("utf-8")
        if sha256(raw) != r["query_sha256"] or parse_qs(urlsplit(r["url"]).query).get("query") != [query]:
            raise ValueError("SPARQL query text/URL/hash mismatch")
        if re.search(r"\b(?:LIMIT|OFFSET|SERVICE)\b", query, re.I):
            raise ValueError("a truncated/federated query cannot claim complete local mapping coverage")


def nace_code(uri):
    if not uri.startswith(NACE2):
        raise ValueError("unexpected NACE URI namespace")
    suffix = uri[len(NACE2):]
    if re.fullmatch(r"[A-Z]|\d{2}", suffix):
        return suffix
    if re.fullmatch(r"\d{3,4}", suffix):
        return suffix[:2] + "." + suffix[2:]
    raise ValueError("NACE URI must identify a source item, not an alias or scheme")


def rdf_nodes(asset):
    groups = defaultdict(list)
    for row_no, row in enumerate(result_rows(asset, ["s", "p", "o"]), 1):
        if row["s"]["type"] != "uri" or row["p"]["type"] != "uri":
            raise ValueError("source URI/predicate must be IRIs")
        groups[row["s"]["value"]].append((row_no, row))
    nodes = []
    for uri, entries in groups.items():
        values, locations = {}, {}
        for index, row in entries:
            p, o = row["p"]["value"], row["o"]
            if p in values:
                raise ValueError("duplicate/multilingual note in English-only source projection")
            values[p], locations[p] = o, index
        code = nace_code(uri)
        if values.get(SKOS + "notation", {}).get("value") != code or values.get(SKOS + "inScheme", {}).get("value") != NACE2 + "nace2":
            raise ValueError("RDF item notation/scheme mismatch")
        if values[SKOS + "inScheme"]["type"] != "uri" or values[SKOS + "prefLabel"].get("xml:lang") != "en":
            raise ValueError("RDF item scheme or English label missing")
        parent = values.get(SKOS + "broader")
        if parent and parent["type"] != "uri":
            raise ValueError("RDF broader endpoint must be URI")
        notes = {name: values.get(XKOS + prop, {}).get("value") for name, prop in
                 (("includes", "coreContentNote"), ("includes_also", "additionalContentNote"), ("excludes", "exclusionNote"))}
        canonical = "NACE:Rev.2:" + code
        nodes.append({"id": canonical + "@cellar-20261109", "canonical_node_id": canonical,
                      "source_id": "NACE", "edition": "Rev.2", "component": asset["evidence"]["resource_id"],
                      "code": code, "source_uri": uri, "label": values[SKOS + "prefLabel"]["value"],
                      "parents": [nace_code(parent["value"])] if parent else [], "parent_origin": "official_RDF_skos_broader",
                      "notes": notes, "definition": "\n\n".join(v for v in notes.values() if v) or None,
                      "original_terms": values, "original_rows": [r for _, r in entries],
                      "field_result_rows": {"notes." + name: locations.get(XKOS + prop) for name, prop in
                                            (("includes", "coreContentNote"), ("includes_also", "additionalContentNote"), ("excludes", "exclusionNote"))},
                      "evidence": {**asset["evidence"], "subject_uri": uri, "result_rows": [i for i, _ in entries]}})
    check = qa([{**n, "code": n["code"]} for n in nodes])
    if any(check[k] for k in ("duplicate_codes", "orphan_parents", "cycles", "self_links")):
        raise ValueError("selected RDF branch hierarchy incomplete")
    return nodes


def reverse_correspondence(asset, current):
    from .furniture import parent_code, topology
    rows = read_workbook(asset["raw"])["Sheet0"]
    if list(rows[0]["cells"].values()) != ["Level", "NACE_Rev_2_Code", "NACE_Rev_2_Title", "NACE_Rev_2_1_Code",
           "NACE_Rev_2_1_Title", "Common_Content", "NumberOfCorresponding_NACE2", "TypeOfMapping", "TypeOfCorrespondence"]:
        raise ValueError("NACE reverse correspondence header changed")
    known = {n["code"]: n for n in current}
    edges = []
    for row in rows[1:]:
        c = row["cells"]
        if c["D"] not in known or (c.get("A") and int(c["A"]) != known[c["D"]]["level"]):
            raise ValueError("reverse current endpoint/level invalid")
        if not c.get("A") and c.get("B"):
            raise ValueError("missing level for a real reverse source endpoint")
        if c.get("B"):
            parent_code(c["B"], "C")
        edges.append({"id": stable_id("mapping", "NACE2-NACE21-published:" + c["B"] + ":" + c["D"]),
                      "from": "NACE:Rev.2:" + c["B"] if c.get("B") else None, "to": "NACE:Rev.2.1:" + c["D"],
                      "level": int(c["A"]) if c.get("A") else None, "target_level": known[c["D"]]["level"], "common_content": c.get("F"),
                      "publisher_correspondence_count": int(c["G"]), "publisher_number_column_label": "NumberOfCorresponding_NACE2",
                      "publisher_mapping_type": c.get("H"), "publisher_correspondence_type": c.get("I"),
                      "original_fields": row, "evidence": {**asset["evidence"], "sheet": "Sheet0", "row": row["row"]}})
    if len({(e["from"], e["to"]) for e in edges}) != len(edges):
        raise ValueError("duplicate reverse correspondence pair")
    topology(edges)
    if any(e["from"] is not None and e["from_degree"] != e["publisher_correspondence_count"] for e in edges):
        raise ValueError("reverse publisher count disagrees with graph; retain misleading G header")
    for e in edges:
        e["publisher_count_check"] = "not_applicable_no_source_endpoint" if e["from"] is None else "agrees_with_observed_outgoing_degree"
    return edges


def xkos_correspondence(asset, predicate_asset, old):
    from .furniture import topology
    groups, relations = defaultdict(list), defaultdict(list)
    known = {n["code"] for n in old}
    for index, row in enumerate(result_rows(asset, ["association", "p", "o"]), 1):
        if row["association"]["type"] != "uri" or row["p"]["type"] != "uri":
            raise ValueError("XKOS association/predicate must be URI")
        groups[row["association"]["value"]].append((index, row))
    for index, row in enumerate(result_rows(predicate_asset, ["s", "p", "o"]), 1):
        if any(row[k]["type"] != "uri" for k in ("s", "p", "o")) or row["p"]["value"] not in MAPPINGS:
            raise ValueError("invalid official SKOS mapping term")
        pair = (row["s"]["value"], row["o"]["value"])
        if relations[pair]:
            raise ValueError("duplicate or competing publisher predicates require separate review")
        relations[pair].append({"predicate_uri": row["p"]["value"], "relation": row["p"]["value"][len(SKOS):],
                                "evidence": {**predicate_asset["evidence"], "result_row": index}, "original_row": row})
    edges = []
    for uri, entries in groups.items():
        values = defaultdict(list)
        for _, row in entries:
            values[row["p"]["value"]].append(row["o"])
        if (len(values[XKOS + "sourceConcept"]) != 1 or len(values[XKOS + "targetConcept"]) != 1
                or values[RDF_TYPE] != [{"type": "uri", "value": XKOS + "ConceptAssociation"}]):
            raise ValueError("XKOS source/target cardinality or association type changed")
        s, t = values[XKOS + "sourceConcept"][0], values[XKOS + "targetConcept"][0]
        if s["type"] != "uri" or t["type"] != "uri" or not t["value"].startswith(UN4):
            raise ValueError("XKOS endpoints must identify NACE2 and ISIC4")
        code = t["value"][len(UN4):]
        if code not in known:
            raise ValueError("unknown ISIC4 endpoint in official XKOS table")
        relation = relations.get((s["value"], t["value"]))
        if not relation:
            raise ValueError("XKOS association missing independently observed publisher SKOS predicate")
        edges.append({"id": stable_id("mapping", "Eurostat-XKOS:" + uri), "association_uri": uri,
                      "from": "NACE:Rev.2:" + nace_code(s["value"]), "to": "ISIC:Rev.4:" + code,
                      "source_uri": s["value"], "target_uri": t["value"],
                      "publisher_relation": relation[0]["relation"], "publisher_predicate": relation[0],
                      "original_terms": dict(values), "original_rows": [r for _, r in entries],
                      "evidence": {**asset["evidence"], "association_uri": uri, "result_rows": [i for i, _ in entries]}})
    pairs = {(e["source_uri"], e["target_uri"]) for e in edges}
    if len(pairs) != len(edges) or pairs != set(relations):
        raise ValueError("XKOS/predicate source coverage differs; no silent missing rows")
    return topology(edges)


def direct_audit(assets, current):
    table_asset = assets["nace-cellar-correspondence-schemes-20261109"]
    tables = result_rows(table_asset, ["g", "table", "scheme", "other"])
    out_asset = assets["nace-cellar-current-mapping-targets-20261109"]
    outgoing = result_rows(out_asset, ["p", "targetNamespace"])
    in_asset = assets["nace-cellar-current-incoming-isic-20261109"]
    incoming = result_rows(in_asset, ["g", "s", "p", "o"])
    control_asset = assets["nace-cellar-current-positive-control-20261109"]
    control = result_rows(control_asset, ["count"])
    if len(control) != 1 or int(control[0]["count"]["value"]) != len(current):
        raise ValueError("direct mapping absence audit lacks matching positive scheme control")
    if any(row["scheme"]["value"] not in (CURRENT, NACE2 + "nace2") for row in tables):
        raise ValueError("correspondence inventory contains unexpected scheme")
    current_tables = [r for r in tables if r["scheme"]["value"] == CURRENT]
    direct = [r for r in current_tables if "isic" in r["other"]["value"].lower()]
    direct_out = [r for r in outgoing if "isic" in r["targetNamespace"]["value"].lower()]
    catalog = json.loads(assets["nace-showvoc-catalog-20261109"]["raw"])["result"]
    if not isinstance(catalog, list) or any(p.get("visibility") != "PUBLIC" for p in catalog):
        raise ValueError("expected a public dataset catalogue only")
    return {"status": "direct_current_link_observed" if direct or direct_out or incoming else "not_observed_in_audited_cellar_snapshot",
            "classification_editions": ["NACE Rev.2.1", "ISIC Rev.5"], "positive_control_current_nodes": int(control[0]["count"]["value"]),
            "catalogue_public_datasets": len(catalog), "catalogue_isic_datasets": [p["name"] for p in catalog if "isic" in p["name"].lower()],
            "correspondence_inventory_rows": len(tables), "distinct_tables_comparing_both_nace_editions": len({r["table"]["value"] for r in tables}),
            "current_tables": sorted({r["table"]["value"] for r in current_tables}),
            "outgoing_mapping_target_namespaces": [r["targetNamespace"]["value"] for r in outgoing],
            "incoming_isic_rows": len(incoming), "current_isic_table_rows": len(direct),
            "evidence": [a["evidence"] for a in (table_asset, out_asset, in_asset, control_asset)],
            "limits": "Finite observed Cellar graphs and publication catalogue; not a publisher statement that no direct table exists anywhere. Empty result alone is never official no-correspondence."}


def compare_publisher_pairs(xkos, legacy):
    xkos_pairs = {(e["from"], e["to"]) for e in xkos}
    unsd_pairs = {(e["to"], e["from"]) for e in legacy}
    return {"only_eurostat": [list(p) for p in sorted(xkos_pairs - unsd_pairs)],
            "only_unsd": [list(p) for p in sorted(unsd_pairs - xkos_pairs)],
            "common_pairs": len(xkos_pairs & unsd_pairs), "resolution": "publisher_variants_retained_no_automatic_reconciliation"}


def sources(root, assets, old, current, forward, legacy):
    check_queries(root, assets)
    nodes = rdf_nodes(assets["nace2-cellar-selected-notes-20261109"])
    reverse = reverse_correspondence(assets["nace2-nace21-correspondence-20260831"], current)
    xkos = xkos_correspondence(assets["nace-cellar-nace2-isic4-xkos-20261109"],
                               assets["nace2-cellar-isic4-predicates-20261109"], old)
    if {(e["from"], e["to"]) for e in reverse} != {(e["to"], e["from"]) for e in forward}:
        raise ValueError("published NACE forward/reverse code-pair sets disagree")
    differences = compare_publisher_pairs(xkos, legacy)
    audit = direct_audit(assets, current)
    stats = {"rdf_selected_nodes": len(nodes), "nace2_to_nace21_rows": len(reverse),
             "xkos_nace2_to_isic4_associations": len(xkos), "publisher_predicates": dict(Counter(e["publisher_relation"] for e in xkos)),
             "forward_reverse_pair_agreement": True, "xkos_unsd_pair_agreement": not differences["only_eurostat"] and not differences["only_unsd"],
             "xkos_unsd_pair_differences": differences, "direct_correspondence_audit": audit}
    return {"nodes": nodes, "reverse": reverse, "xkos": xkos, "statistics": stats}


def extend_plan(root, original):
    followup = read_json(root / PLAN)
    if sha256((root / "data/research/furniture-review.json").read_bytes()) != followup["parent_review_sha256"]:
        raise ValueError("parent furniture review changed")
    result = copy.deepcopy(original)
    for key in ("claims", "navigation", "activities", "official_reviews", "research_mappings"):
        identity = "mapping_id" if key == "official_reviews" else "id"
        known = {x[identity] for x in result[key]}
        for item in followup.get(key, []):
            if item[identity] in known:
                raise ValueError("follow-up tries to replace existing stable identity/review")
            result[key].append(copy.deepcopy(item))
            known.add(item[identity])
    by_id = {a["id"]: a for a in result["activities"]}
    for update in followup.get("binding_decisions", []):
        activity = by_id[update["atlas_id"]]
        old = next(b for b in activity.get("candidate_source_bindings", []) if b["node_id"] == update["node_id"])
        if sha256(json.dumps(old, sort_keys=True, ensure_ascii=False).encode()) != update["previous_binding_sha256"]:
            raise ValueError("candidate binding decision no longer matches previous pending record")
        activity.setdefault("binding_history", []).append({"node_id": old["node_id"], "previous_binding": copy.deepcopy(old),
                  "decision_id": update["id"], "status": "approved_bounded_allocation", "claim_ids": update["binding"]["claim_ids"],
                  "reason": update["rationale"], "recorded_on": followup["reviewed_on"]})
        activity["candidate_source_bindings"].remove(old)
        activity["source_bindings"].append(copy.deepcopy(update["binding"]))
    issues = {i["id"]: i for i in result["issues"]}
    for update in followup["issue_followups"]:
        issue = issues[update["issue_id"]]
        issue.setdefault("history", []).append({k: copy.deepcopy(v) for k, v in issue.items() if k != "history"})
        issue.update(status=update["status"], followup=copy.deepcopy(update))
    for issue in followup.get("new_issues", []):
        if issue["id"] in issues:
            raise ValueError("follow-up issue replaces previous issue")
        result["issues"].append(copy.deepcopy(issue))
        issues[issue["id"]] = issue
    result["comparison_decisions"] = followup["comparison_decisions"]
    for update in followup.get("research_mapping_followups", []):
        mapping = next(m for m in result["research_mappings"] if m["id"] == update["mapping_id"])
        mapping.setdefault("history", []).append({k: copy.deepcopy(v) for k, v in mapping.items() if k != "history"})
        mapping["activity_ids"] = sorted(set(mapping["activity_ids"] + update["additional_activity_ids"]))
    result["followup_metadata"] = {"reviewed_input_sha256": followup["reviewed_input_sha256"], "review_sha256": sha256((root / PLAN).read_bytes()),
                                   "parent_review_sha256": followup["parent_review_sha256"], "reviewed_on": followup["reviewed_on"]}
    return result


def supports_binding(binding, claims, documents, activity):
    key = binding["node_id"]
    for cid in binding["claim_ids"]:
        c = claims[cid]
        doc = documents[c["document"]]
        if (doc.get("canonical_node_id", c["document"]) == key and c["role"] == "inclusion"):
            return True
        if c["role"] == "official_activity_allocation":
            # This is an explicit publisher allocation, not a composed chain or a name match.
            if (c.get("allocated_node_id") != key or c.get("activity_key") != activity["key"]
                    or c["field"] != "common_content" or key not in (doc.get("from"), doc.get("to"))
                    or doc["evidence"]["resource_id"] not in ("nace21-nace2-correspondence", "nace2-nace21-correspondence-20260831")):
                raise ValueError("invalid publisher activity allocation evidence")
            if binding.get("basis") != "explicit_official_crosswalk_activity_allocation":
                raise ValueError("allocation evidence must not masquerade as direct source inclusion")
            return True
    return False
