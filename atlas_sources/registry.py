import csv
import json
import re
from pathlib import Path


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def load(root):
    registry = read_json(root / "data/registry/sources.json")
    resources = read_json(root / "data/registry/resources.json")
    return registry, resources


def validate(root):
    registry, resources = load(root)
    errors = []
    ids = [s["id"] for s in registry["sources"]]
    domains = {d["id"] for d in registry["domains"]}
    if len(set(ids)) != len(ids):
        errors.append("duplicate source IDs")
    with (root / "data/source-candidates.csv").open(encoding="utf-8") as stream:
        original = {r["id"] for r in csv.DictReader(stream)}
    if original - set(ids):
        errors.append(f"missing original candidates: {sorted(original - set(ids))}")
    for s in registry["sources"]:
        for field in ("name", "classification_object", "publisher", "editions", "hierarchy",
                      "license", "download", "official_mappings", "evidence", "unresolved"):
            if field not in s:
                errors.append(f"{s['id']}: missing {field}")
        if not set(s["domains"]) <= domains:
            errors.append(f"{s['id']}: unknown domain")
        if not s["evidence"] or any(not e.get("url", "").startswith("https://")
                                    for e in s["evidence"]):
            errors.append(f"{s['id']}: missing evidence URL")
        if s["verification_status"] == "verified_metadata" and s["unresolved"]:
            errors.append(f"{s['id']}: verified despite unresolved metadata")
    seen = set()
    for r in resources:
        if r["id"] in seen:
            errors.append(f"duplicate resource {r['id']}")
        seen.add(r["id"])
        for field in ("id", "source_id", "edition", "filename"):
            if not re.fullmatch(r"[A-Za-z0-9_.-]+", r[field]) or r[field] in (".", ".."):
                errors.append(f"unsafe {field}: {r[field]}")
        if r["source_id"] not in ids:
            errors.append(f"{r['id']}: unknown source")
        elif r["edition"] not in {e["id"] for e in registry["sources"][ids.index(r["source_id"])]["editions"]}:
            errors.append(f"{r['id']}: unknown edition")
        if not r["url"].startswith("https://"):
            errors.append(f"{r['id']}: HTTPS required")
        if r["rights"]["redistribute"] is True and not r["rights"].get("evidence_url"):
            errors.append(f"{r['id']}: redistribution needs evidence")
    return errors
