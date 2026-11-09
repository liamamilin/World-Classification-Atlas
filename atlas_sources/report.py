"""Deterministic reports rebuilt from the registry, pinned raw bytes and integrity checks."""
import json
from collections import Counter
from pathlib import Path
from .normalize import inspect
from .registry import read_json, write_json


def build(root, registry, resources):
    integrity = inspect(root, resources)
    economy_path = root / "data/reports/isic-economy.json"
    economy = read_json(economy_path) if economy_path.exists() else None
    if economy and economy.get("status") == "passed":
        pins = read_json(root / "data/resources.lock.json")
        local = {r["resource_id"]: r for r in integrity}
        if any(local.get(e["resource_id"], {}).get("status") in ("failed", "not_downloaded") for e in economy["inputs"]):
            economy = {"status": "inputs_not_available_locally", "note": "Collect and run economy to reproduce this research locally."}
        elif any(pins.get(e["resource_id"], {}).get("sha256") != e["sha256"] for e in economy["inputs"]):
            economy = {"status": "stale", "note": "Run economy again after input pins changed."}
        else:
            stages = {"isic4-database": {"status": "notes_parsed", "nodes": economy["rev4"]["node_count"]},
                      "isic5-notes-20260819": {"status": "notes_parsed", "nodes": economy["rev5"]["node_count"]},
                      "isic4-isic5-correspondence": {"status": "correspondence_parsed", "rows": economy["correspondence"]["rows"]}}
            stages.update({p["resource_id"]: {"status": "text_extracted", "pages": p["pages"]} for p in economy["pdfs"]})
            if economy.get("auxiliary_product_evidence"):
                stages["cpc21-notes-20250403"] = {"status": "selected_auxiliary_product_evidence",
                    **economy["auxiliary_product_evidence"]}
            for row in integrity:
                if row["resource_id"] in stages:
                    row["domain_stage"] = stages[row["resource_id"]]
    snapshots = [r for r in integrity if r.get("sha256") and r["status"] != "failed"]
    furniture_path = root / "data/reports/furniture-alignment.json"
    furniture = read_json(furniture_path) if furniture_path.exists() else None
    if furniture and furniture.get("status") == "passed":
        pins = read_json(root / "data/resources.lock.json")
        local = {r["resource_id"]: r for r in integrity}
        if any(local.get(e["resource_id"], {}).get("status") in ("failed", "not_downloaded") for e in furniture["inputs"]):
            furniture = {"status": "inputs_not_available_locally"}
        elif any(pins.get(e["resource_id"], {}).get("sha256") != e["sha256"] for e in furniture["inputs"]):
            furniture = {"status": "stale"}
        else:
            stages = {"nace21-notes-20260930": {"status": "structure_and_notes_parsed", "nodes": furniture["nace21"]["node_count"]},
                      "nace21-nace2-correspondence": {"status": "correspondence_parsed", "rows": furniture["official_tables"]["nace21_to_nace2_rows"]},
                      "isic4-nace2-correspondence": {"status": "correspondence_parsed", "rows": furniture["official_tables"]["isic4_to_nace2_rows"]},
                      "nace2-manual-2008": {"status": "selected_branch_notes_parsed", "nodes": furniture["nace2_selected"]["node_count"]},
                      "nace21-manual-2026": {"status": "text_extracted_and_selected_clauses_reviewed"}}
            followup = furniture.get("followup_sources")
            if followup:
                stages.update({"nace2-nace21-correspondence-20260831": {"status": "published_reverse_correspondence_parsed", "rows": followup["nace2_to_nace21_rows"]},
                               "nace2-cellar-selected-notes-20261109": {"status": "selected_RDF_component_parsed", "nodes": followup["rdf_selected_nodes"]},
                               "nace-cellar-nace2-isic4-xkos-20261109": {"status": "official_direct_XKOS_correspondence_parsed", "associations": followup["xkos_nace2_to_isic4_associations"]},
                               "nace2-cellar-isic4-predicates-20261109": {"status": "publisher_SKOS_predicates_preserved", "predicates": followup["publisher_predicates"]}})
                for rid in ("nace-cellar-correspondence-schemes-20261109", "nace-cellar-current-mapping-targets-20261109",
                            "nace-cellar-current-incoming-isic-20261109", "nace-cellar-current-positive-control-20261109"):
                    stages[rid] = {"status": "bounded_direct_correspondence_audit", "finding": followup["direct_correspondence_audit"]["status"]}
            if furniture.get("material_boundaries"):
                stages["isic5-notes-20240311"] = {"status": "historical_note_clauses_reviewed",
                    "pages": furniture["material_boundaries"]["pdf_pages"]["isic5-notes-20240311"]}
            if furniture.get("contract_parts_boundaries"):
                contract = furniture["contract_parts_boundaries"]
                stages["uk-sic-2007-index-202409"] = {"status": "selected_activity_index_rows_reviewed",
                    "index_rows": contract["uk_index_activity_rows"], "selected_rows": contract["uk_index_selected_rows"]}
                for rid, pages in contract["pdf_pages"].items():
                    stages[rid] = {"status": "selected_clauses_reviewed", "pages": pages}
                for rid in contract["publisher_release_recheck"]["listings"]:
                    stages[rid] = {"status": "publisher_release_listing_checked"}
            if furniture.get("naf_boundary"):
                naf = furniture["naf_boundary"]
                stages.update({
                    "naf-rev2-hierarchy": {"status": "official_hierarchy_parsed", "nodes": naf["rev2"]["node_count"]},
                    "naf-2025-structure-202610": {"status": "official_hierarchy_parsed", "nodes": naf["naf2025"]["node_count"]},
                    "naf-rev2-cpf21-notes-2020": {"status": "selected_activity_notes_parsed"},
                    "naf-2025-notes-2025": {"status": "selected_activity_notes_parsed"},
                    "naf-rev2-to-2025-202610": {"status": "official_correspondence_parsed", "rows": naf["correspondence"]["forward_rows"]},
                    "naf-2025-to-rev2-202610": {"status": "official_correspondence_parsed", "rows": naf["correspondence"]["reverse_rows"]},
                })
            for row in integrity:
                if row["resource_id"] in stages:
                    row["domain_stage"] = stages[row["resource_id"]]
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
               "economic_activity_research": ({"status": economy["status"], "report": "data/reports/isic-economy.json",
                                                "curation": economy.get("curation"), "expanded_review": economy.get("expanded_review"),
                                                "priority_review": economy.get("priority_review"),
                                                "auxiliary_product_evidence": economy.get("auxiliary_product_evidence"),
                                                "correspondence": economy.get("correspondence")}
                                               if economy else None),
               "counts_note": "Counts are per resource, not global concepts. O*NET CSV/CTDL overlap. ISIC has a separately counted reviewed subset; no instance links.",
               "furniture_multisource_research": ({k: furniture[k] for k in ("status", "nace21", "official_tables", "directory", "reused_ids", "new_ids", "bounded_activities", "evidence_claims", "research_mappings", "candidate_bindings", "followup_sources", "activity_review_status", "binding_history_records", "approved_isic5_source_levels", "material_boundaries", "contract_parts_boundaries", "naf_boundary") if k in furniture} if furniture else None),
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
        stage = f"; economy: {r['domain_stage']}" if r.get("domain_stage") else ""
        lines.append(f"| {r['resource_id']} | {r['edition']} | {r['status']}{stage} | {count} | {r.get('definitions', '—')} |")
    if economy:
        lines += ["", "经济活动专项结果另见 [ISIC 实测报告](isic-economy.json)：包含完整注释解析、官方对应表及已审研究概念。上表 status 为通用格式/结构检查，economy 字段表示专项处理。"]
        if economy.get("expanded_review"):
            review = economy["expanded_review"]
            lines += ["", f"经济活动局部目录：{review['reviewed_rev5_classes']} 个已审类范围锚点、{review['directory_kinds']['source_derived_navigation']} 个仅作导航的上级；"
                      f"{review['mapping_status']['reviewed_current_relation']} 条已审当前关系。所有605行仍保留原始版本和审查队列，"
                      "详见 [扩展审查](isic-expanded-review.json)。上级导航不计作已审语义覆盖。"]
            if economy.get("priority_review"):
                focused = economy["priority_review"]
                lines += ["", f"植物奶/食用冰/纺织/核燃料专项：{focused['bounded_activities']} 个Atlas自有活动子节点，"
                          f"{focused['official_rows_reviewed']} 条官方行的活动范围审查；另有"
                          f"{review['supplemental_mapping_status'].get('accepted_scoped_overlap', 0)} 条已审研究补充和"
                          f"{review['supplemental_mapping_status'].get('held_after_research', 0)} 条待审研究候选。"
                          "补充关系独立于官方表，见 [优先问题证据报告](isic-priority-review.json)。"]
                lines += ["", f"其中{review.get('current_only_activities', 0)}个活动只审定Rev.5当前范围；"
                          f"{review.get('candidate_source_bindings', 0)}条待审来源关联与已审绑定分别索引，"
                          f"{review.get('held_directory_proposals', 0)}个待审目录提案不计入已审节点。"
                          "CPC产品说明和主要行业对应仅作旁证，见 [边界核查](isic-boundary-review.json)。"]
    if furniture:
        lines += ["", "家具多源研究另见 [NACE/ISIC实测](furniture-alignment.json)，状态：" + furniture["status"] + "。"]
        if furniture.get("status") == "passed":
            lines += [f"NACE Rev.2.1完整解析{furniture['nace21']['node_count']}节点；家具分支{furniture['directory']['node_count']}节点，含{furniture['reused_ids']}个沿用身份及{furniture['new_ids']}个新身份；"
                      f"{furniture['research_mappings']}条有界跨体系研究关系、{furniture['official_tables']['individually_reviewed_rows']}条官方行独立审查、{furniture['candidate_bindings']}条待审来源绑定。"
                      "原有ISIC目录仍独立保留，节点数不重复累加。上表通用适配器数量不包含专项解析。"]
            if furniture.get("followup_sources"):
                focused = furniture["followup_sources"]
                lines += [f"新增旧NACE2→ISIC4直接官方XKOS桥{focused['xkos_nace2_to_isic4_associations']}条，发布者closeMatch保持独立；"
                          f"与UNSD有{focused['xkos_unsd_pair_differences']['common_pairs']}对代码事实一致，46.6→466/465差异保留。"
                          "当前NACE2.1–ISIC5审计有1047节点阳性对照，未观察到直接关系。"]
            if furniture.get("material_boundaries"):
                material = furniture["material_boundaries"]
                lines += [f"家具材料边界研究含{material['new_activities']}项活动和{material['new_claims']}条证据。"
                          f"在{len(material['official_pair_comparisons'])}份固定官方表中核实卫生洁具缺行，单独登记定义支持的研究对应。"]
            if furniture.get("contract_parts_boundaries"):
                contract = furniture["contract_parts_boundaries"]
                recheck = contract["publisher_release_recheck"]
                lines += [f"承包处理与旧家具部件新增{contract['new_activities']}项活动和{contract['new_claims']}条证据。"
                          f"发布复查中{len(recheck['same_bytes'])}份文件字节与旧快照相同，核查{recheck['registry_titles_checked']}条登记标题。"
                          "卫生洁具官方缺行、旧31.01冲突及专用店铺部件的旧ISIC候选继续保留。"]
            if furniture.get("naf_boundary"):
                naf = furniture["naf_boundary"]
                correspondence = naf["correspondence"]
                lines += [f"法国NAF两版五级目录解析{naf['rev2']['node_count']}和{naf['naf2025']['node_count']}个节点。"
                          f"双向官方对应各{correspondence['forward_rows']}及{correspondence['reverse_rows']}行，保留原方向内容。"
                          f"本次增补{naf['new_activities']}项家具活动和{naf['new_claims']}条逐条证据。"
                          "法国国家表的卫生洁具与陶瓷厨卫家具分别对应，原ISIC缺行仍独立登记。"]
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
