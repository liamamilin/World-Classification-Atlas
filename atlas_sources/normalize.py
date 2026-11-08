import csv
import io
import json
import re
import zipfile
from collections import Counter
from .acquire import check_payload, sha256, snapshot_dir
from .registry import read_json, write_json


def table_nodes(data, resource):
    text = data.decode(resource["encoding"], errors="strict")
    parser = resource["parser"]
    nodes = []
    section = None
    if parser == "un_dotted":
        rows = []
        lines = text.splitlines()
        if not lines or not re.fullmatch(r"Code\s+Description", lines[0].strip()):
            raise ValueError("unexpected fixed-width header")
        for line_no, line in enumerate(lines[1:], 2):
            if not line.strip():
                continue
            match = re.fullmatch(r"(\d{2}(?:\.\d){0,2})\s+(.+)", line)
            if not match:
                raise ValueError(f"unparsed row {line_no}: {line!r}")
            rows.append((line_no, {"Code": match[1], "Description": match[2]}))
    else:
        reader = csv.DictReader(io.StringIO(text, newline=""))
        headers = {
            "un_isic": (["ISIC Rev 5 Code", "ISIC Rev 5 Title"] if resource["edition"] == "Rev.5"
                        else ["Code", "Description"]),
            "un_numeric": ["CPC Ver. 3.0  Code", "CPC Ver. 3.0 Title"],
            "onet_occupations": ["O*NET-SOC Code", "Title", "Description"],
            "onet_content": ["Element ID", "Element Name", "Description"],
        }[parser]
        if reader.fieldnames != headers:
            raise ValueError(f"unexpected CSV headers: {reader.fieldnames!r}; expected {headers!r}")
        rows = []
        for row in reader:
            if None in row or any(value is None for value in row.values()):
                raise ValueError(f"malformed CSV row ending at line {reader.line_num}: {row!r}")
            rows.append((reader.line_num, row))
    for line_no, original in rows:
        fields = list(original.values())
        code, label = fields[0], fields[1]
        definition = fields[2] if parser.startswith("onet_") else None
        if not code or not label:
            raise ValueError(f"missing code or label at line {line_no}")
        parent = None
        if parser == "un_isic":
            if re.fullmatch("[A-Z]", code):
                section = code
            elif re.fullmatch(r"\d{2,4}", code):
                parent = section if len(code) == 2 else code[:-1]
                if parent is None:
                    raise ValueError(f"division before section: {code}")
            else:
                raise ValueError(f"unexpected ISIC code {code!r}")
        elif parser == "un_numeric":
            if not re.fullmatch(r"\d{1,5}", code):
                raise ValueError(f"unexpected CPC code {code!r}")
            parent = code[:-1] or None
        elif parser in ("un_dotted", "onet_content"):
            parent = code.rpartition(".")[0] or None
        elif parser == "onet_occupations" and not re.fullmatch(r"\d{2}-\d{4}\.\d{2}", code):
            raise ValueError(f"unexpected O*NET code {code!r}")
        nodes.append({"code": code, "label": label, "definition": definition,
                      "definition_origin": "official_file" if definition else None,
                      "parents": [parent] if parent else [],
                      "parent_origin": "official_code_structure_and_row_order" if parent else None,
                      "source_row": line_no, "original_fields": original})
    return nodes


def graph_nodes(data):
    graph = json.loads(data)["@graph"]
    collections = [x for x in graph if x.get("@type") == "ceterms:Collection"]
    members = {uri for x in collections for uri in x.get("ceterms:hasMember", [])}
    nodes = []
    for obj in graph:
        if obj.get("@type") == "ceterms:Collection":
            continue
        if obj.get("@type") != "ceterms:Occupation":
            raise ValueError(f"unexpected CTDL type {obj.get('@type')!r}")
        if obj["@id"] not in members:
            raise ValueError(f"occupation not in collection: {obj['@id']}")
        nodes.append({"code": obj["ceterms:codedNotation"], "label": obj["ceterms:name"]["en-US"],
                      "definition": obj["ceterms:description"]["en-US"],
                      "definition_origin": "official_file", "source_uri": obj["@id"],
                      "parents": [], "parent_origin": None, "original_fields": obj})
    if members != {x["source_uri"] for x in nodes}:
        raise ValueError("collection member loss")
    return nodes


def qa(nodes):
    codes = Counter(n["code"] for n in nodes)
    duplicates = sorted(c for c, count in codes.items() if count > 1)
    by_code = {n["code"]: n for n in nodes}
    orphans, self_links, cycles = [], [], []
    colors, depths = {}, {}

    def visit(code, path):
        if colors.get(code) == 1:
            cycles.append(path + [code])
            return 0
        if colors.get(code) == 2:
            return depths[code]
        colors[code] = 1
        parent_depths = [visit(p, path + [code]) for p in by_code[code]["parents"] if p in by_code]
        depths[code] = max(parent_depths, default=0) + 1
        colors[code] = 2
        return depths[code]

    for n in nodes:
        for parent in n["parents"]:
            if parent not in by_code:
                orphans.append({"code": n["code"], "parent": parent})
            if parent == n["code"]:
                self_links.append(n["code"])
    for code in by_code:
        visit(code, [])
    parents = {p for n in nodes for p in n["parents"]}
    return {"node_count": len(nodes), "unique_codes": len(codes), "duplicate_codes": duplicates,
            "edge_count": sum(len(n["parents"]) for n in nodes), "orphan_parents": orphans,
            "self_links": self_links, "cycles": cycles,
            "levels": dict(sorted(Counter(depths.values()).items())),
            "roots": sum(not n["parents"] for n in nodes),
            "leaves": sum(n["code"] not in parents for n in nodes),
            "definitions": sum(bool(n.get("definition")) for n in nodes),
            "deprecated_or_alias_status": "not_supplied_by_these_adapters",
            "polyhierarchy_nodes": sum(len(n["parents"]) > 1 for n in nodes)}


def inspect(root, resources, write=False):
    lockfile = root / "data/resources.lock.json"
    lock = read_json(lockfile) if lockfile.exists() else {}
    results = []
    for resource in resources:
        result = {"resource_id": resource["id"], "source_id": resource["source_id"],
                  "edition": resource["edition"], "role": resource["role"]}
        try:
            pinned = lock.get(resource["id"])
            if not pinned:
                result["status"] = "blocked_rights" if resource["rights"]["local_processing"] is not True else "not_downloaded"
                results.append(result)
                continue
            folder = snapshot_dir(root, resource, pinned["sha256"])
            path = folder / resource["filename"]
            if not path.exists():
                result.update(status="not_downloaded", expected_sha256=pinned["sha256"])
                results.append(result)
                continue
            data = path.read_bytes()
            manifest = read_json(folder / "manifest.json")
            if (sha256(data) != pinned["sha256"] or manifest["sha256"] != pinned["sha256"]
                    or manifest["url"] != resource["url"] or pinned["url"] != resource["url"]
                    or manifest["source_id"] != resource["source_id"] or manifest["edition"] != resource["edition"]):
                raise ValueError("snapshot/manifest/lock provenance mismatch")
            check_payload(data, resource)
            result.update(sha256=pinned["sha256"], path=str(path.relative_to(root)), bytes=len(data))
            if not resource.get("parser"):
                result.update(status="format_checked_only", note="No semantic adapter; no node counts or edition confirmation inferred.")
            else:
                nodes = graph_nodes(data) if resource["parser"] == "ctdl_taxonomy" else table_nodes(data, resource)
                result.update(qa(nodes))
                expected = resource.get("expected_rows")
                result["publisher_expected_rows"] = expected
                result["publisher_count_match"] = len(nodes) == expected if expected is not None else None
                result["hierarchy_coverage"] = "flat_file_no_parent_edges" if resource["parser"] in ("onet_occupations", "ctdl_taxonomy") else "code_structure_reconstructed"
                if (not nodes or result["duplicate_codes"] or result["orphan_parents"] or result["self_links"]
                        or result["cycles"] or result["publisher_count_match"] is False):
                    raise ValueError("node integrity or publisher count check failed; see QA fields")
                result["status"] = "parsed"
                if write:
                    output_base = root / ("data/normalized" if resource["rights"]["redistribute"] is True else "data/local/normalized")
                    target = output_base / resource["source_id"] / resource["edition"] / resource["id"] / pinned["sha256"] / "nodes.jsonl"
                    target.parent.mkdir(parents=True, exist_ok=True)
                    provenance = {"source_id": resource["source_id"], "edition": resource["edition"],
                                  "resource_id": resource["id"], "raw_sha256": pinned["sha256"]}
                    target.write_text("".join(json.dumps({**provenance, **n}, ensure_ascii=False) + "\n" for n in nodes), encoding="utf-8")
                    result["normalized_path"] = str(target.relative_to(root))
        except (OSError, ValueError, KeyError, csv.Error, RecursionError, zipfile.BadZipFile) as error:
            result.update(status="failed", error=f"{type(error).__name__}: {error}")
            if write:
                write_json(root / "data/reports/rejected" / (resource["id"] + ".json"), result)
        results.append(result)
    return results


def process(root, resources, write=False):
    results = inspect(root, resources, write=write)
    write_json(root / "data/reports/integrity.json", results)
    for r in results:
        print(f"{r['resource_id']}: {r['status']}" + (f" ({r['node_count']} nodes)" if "node_count" in r else ""))
    return int(any(r["status"] in ("failed", "not_downloaded") for r in results))
