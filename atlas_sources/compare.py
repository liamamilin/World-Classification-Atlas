"""Syntactic source research only; never emit concept mappings or equivalence claims."""
from .acquire import sha256, snapshot_dir
from .normalize import graph_nodes, table_nodes
from .registry import read_json

PAIRS = [("01-economy", "isic4-structure", "isic5-structure"),
         ("03-consumption", "cofog1999-structure", "copni1999-structure"),
         ("05-occupations", "onet2019-taxonomy", "onet31-occupations")]


def compare_nodes(first, second):
    a, b = {n["code"]: n for n in first}, {n["code"]: n for n in second}
    common = set(a) & set(b)
    comparable = {c for c in common if a[c].get("definition") and b[c].get("definition")}
    return {"from_count": len(a), "to_count": len(b), "shared_code_strings": len(common),
            "only_from": len(set(a) - set(b)), "only_to": len(set(b) - set(a)),
            "shared_codes_with_changed_label": sum(a[c]["label"] != b[c]["label"] for c in common),
            "shared_codes_with_both_definitions": len(comparable),
            "shared_codes_with_changed_definition": sum(a[c]["definition"] != b[c]["definition"] for c in comparable),
            "semantic_equivalence_inferred": False}


def build_comparisons(root, resources):
    lockfile = root / "data/resources.lock.json"
    lock = read_json(lockfile) if lockfile.exists() else {}
    results, cache = [], {}
    for domain, first, second in PAIRS:
        row = {"domain": domain, "from_resource": first, "to_resource": second}
        try:
            for rid in (first, second):
                if rid not in cache:
                    r = next(r for r in resources if r["id"] == rid)
                    data = (snapshot_dir(root, r, lock[rid]["sha256"]) / r["filename"]).read_bytes()
                    if sha256(data) != lock[rid]["sha256"]:
                        raise ValueError(f"raw hash mismatch: {rid}")
                    cache[rid] = graph_nodes(data) if r["parser"] == "ctdl_taxonomy" else table_nodes(data, r)
            row.update(status="compared", **compare_nodes(cache[first], cache[second]))
        except (OSError, KeyError, ValueError, StopIteration) as error:
            row.update(status="unavailable", error=f"{type(error).__name__}: {error}")
        results.append(row)
    return {"note": "Syntactic comparisons only. Equal codes or labels are not proof of semantic equivalence; missing definitions are not compared. No fusion or inferred mappings.",
            "comparisons": results}
