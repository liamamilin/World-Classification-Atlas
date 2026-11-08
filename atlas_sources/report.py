"""Deterministic reports rebuilt from the registry, pinned raw bytes and integrity checks."""
import json
from collections import Counter
from pathlib import Path
from .normalize import inspect
from .registry import read_json, write_json


def build(root, registry, resources):
    integrity = inspect(root, resources)
    snapshots = [r for r in integrity if r.get("sha256") and r["status"] != "failed"]
    parsed = [r for r in integrity if r["status"] == "parsed"]
    source_ids = {r["source_id"] for r in snapshots}
    domains = []
    for domain in registry["domains"]:
        sources = [s for s in registry["sources"] if domain["id"] in s["domains"]]
        domains.append({**domain, "registered": len(sources),
                        "metadata_status": dict(Counter(s["verification_status"] for s in sources)),
                        "sources_with_local_files": len({s["id"] for s in sources} & source_ids),
                        "sources_with_parsed_files": len({s["id"] for s in sources} & {r["source_id"] for r in parsed})})
    family_path = root / "data/discovery/unsd-family.json"
    family_count = read_json(family_path)["parsed_count"] if family_path.exists() else None
    summary = {"review_date": registry["review_date"], "registered_sources": len(registry["sources"]),
               "metadata_status": dict(Counter(s["verification_status"] for s in registry["sources"])),
               "domains": domains, "unsd_family_discovered_candidates": family_count,
               "planned_resources": len(resources), "pinned_resources": len(snapshots),
               "sources_with_local_files": len(source_ids), "parsed_resources": len(parsed),
               "resource_status": dict(Counter(r["status"] for r in integrity)),
               "counts_note": "Counts are per resource, not deduplicated global concepts. O*NET CSV and CTDL overlap. No Atlas fusion or instance links.",
               "resources": integrity}
    reports = root / "data/reports"
    write_json(reports / "coverage.json", summary)
    write_json(reports / "integrity.json", integrity)
    from .compare import build_comparisons
    write_json(reports / "domain-comparisons.json", build_comparisons(root, resources))
    lines = ["# 来源与采集覆盖", "", f"核查日期：{registry['review_date']}。来源核实与下载状态独立。", "",
             f"登记 {len(registry['sources'])} 个来源；覆盖 {len(domains)} 个导航领域。UNSD Family 独立发现 {family_count} 条候选，未经逐条核实，不能与注册表相加。", "",
             f"{len(resources)} 个采集任务，{len(snapshots)} 个已锁定且通过格式检查，涉及 {len(source_ids)} 个来源；{len(parsed)} 个资源可解析。", "",
             "| 领域 | 登记 | 有本地文件的来源 | 已解析的来源 |", "|---|---:|---:|---:|"]
    for d in domains:
        lines.append(f"| {d['id']} {d['label']} | {d['registered']} | {d['sources_with_local_files']} | {d['sources_with_parsed_files']} |")
    lines += ["", "## 文件实测", "", "| 资源 | 版本 | 状态 | 节点/层级分布 | 定义 |", "|---|---|---|---|---:|"]
    for r in integrity:
        count = f"{r['node_count']} / {r['levels']}" if "node_count" in r else "未统计"
        lines.append(f"| {r['resource_id']} | {r['edition']} | {r['status']} | {count} | {r.get('definitions', '—')} |")
    lines += ["", "节点数按实际原文件统计，不能跨表累加为世界概念总量。O*NET 两种职业资源包含重复代码；职业文件不提供父子边，未据代码补造缺失父节点。",
              "", "## 未决项（逐来源）", ""]
    for s in registry["sources"]:
        if s["unresolved"]:
            lines.append(f"- {s['id']}: " + "；".join(s["unresolved"]) + f"。 [官方入口]({s['official_url']})")
    (reports / "coverage.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    # Inline metadata only, so file:// works offline; raw restricted source content is never embedded.
    template = (Path(__file__).parent / "registry_view.html").read_text(encoding="utf-8")
    payload = json.dumps({"registry": registry, "coverage": summary}, ensure_ascii=False).replace("<", "\\u003c")
    (reports / "registry.html").write_text(template.replace("__ATLAS_DATA__", payload), encoding="utf-8")
    print(f"Report: {reports / 'coverage.md'}\nBrowse: {reports / 'registry.html'}")
