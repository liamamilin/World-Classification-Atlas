"""Reviewed trade-goods sample built from pinned CPC clauses and WCO passages."""
from collections import Counter

from .cpc_hs_followup import pdf_excerpt
from .isic import stable_id
from .normalize import qa

PUBLIC = "data/atlas/products/trade-goods-directory.json"
SCHEME = "urn:atlas:scheme:trade-goods"
NAVIGATION = (
    ("trade-goods", None, "贸易商品", "按商品形态、用途和工艺组织的 Atlas 样板。"),
    ("lighting", "trade-goods", "照明商品", "按用途和光源设计区分灯串与其他电灯具。"),
    ("tree-lights", "lighting", "圣诞树用灯串", "按是否仅为 LED 光源设计分开。"),
    ("seafood", "trade-goods", "水产商品", "按物种和加工形态组织，当前选取冷冻章鱼候选。"),
    ("coal", "trade-goods", "煤炭商品", "保留商品形态、煤种及判定口径的差异。"),
    ("cycles", "trade-goods", "摩托车及装辅助动力的脚踏车", "按驱动和边车范围组织有证据的样本。"),
)

# A leaf is a curated scope, with one WCO anchor and explicit CPC clause bindings.
# A missing relation marks a pending binding. Reviewed exclusions are kept separately from positive matches.
LEAVES = (
    ("tree-lights-led-only", "tree-lights", "LED 专用圣诞树灯串",
     "仅为 LED 光源设计的圣诞树用灯串。", "9405.31", "christmas-strings",
     (("46533", "C", "definition", "source_broader", "该 CPC 子类还涵盖其他 LED 专用灯具。"),
      ("46532", "D", "exclusion", "excluded", "CPC 排除句明确列出 9405.31。"))),
    ("tree-lights-other", "tree-lights", "其他圣诞树灯串",
     "圣诞树用灯串中，未限定为仅使用 LED 光源的部分。", "9405.39", "christmas-strings",
     (("46532", "C", "definition", "exact", "CPC 定义指向 9405.39，并明确排除同组 LED 专用灯串。"),)),
    ("other-photovoltaic-led", "lighting", "其他光伏 LED 专用电灯具",
     "归在其他电灯及灯具中的光伏产品，仅为 LED 光源设计。", "9405.41", "other-electric-lighting",
     (("46533", "C", "definition", "source_broader", "该 CPC 子类还涵盖其他用途的 LED 专用灯具。"),
      ("46539", "D", "exclusion", "excluded", "CPC 排除句明确列出 9405.41。"))),
    ("other-led-scope-review", "lighting", "其他 LED 专用电灯具对应待核",
     "核查 HS 所列的其他 LED 专用电灯具，与 CPC 原句所指范围的差异。", "9405.42", "other-electric-lighting",
     (("46539", "C", "definition", None, "CPC 标题限定非 LED 专用，所引的 9405.42 却明确限定 LED 专用。"),)),
    ("frozen-octopus-candidate", "seafood", "冷冻章鱼对应待核",
     "核查冷冻章鱼部分。章鱼粉、粗粉及团粒另有 HS 章注边界。", "0307.52", "octopus",
     (("21267", "C", "definition", None, "CPC 原句写 0307.53。0307.52 有冷冻章鱼税则依据，保留为候选。"),)),
    ("unagglomerated-bituminous-scope-review", "coal", "未团聚烟煤共引范围待核",
     "以 WCO 未团聚煤分组和烟煤阈值为边界，记录烟煤与次烟煤两个 CPC 条目的共引问题。",
     "2701.12", "bituminous-coal",
     (("11012", "C", "definition", None, "烟煤原句明确引用该码，两条 CPC 原句的共引范围待核。"),
      ("11031", "C", "definition", None, "次烟煤位于 CPC 褐煤类，其引用与烟煤共用同一 HS 子目。"))),
    ("electric-motor-cycles", "cycles", "电动机驱动的摩托车及辅助动力脚踏车",
     "HS 87.11 内以电动机驱动的摩托车和装有辅助动力的脚踏车，可带边车。", "8711.60", "motorcycles",
     (("49913", "C", "inclusion", "source_broader", "纳入原句点名电驱动，CPC 子类标题还涵盖更宽的辅助动力及边车范围。"),)),
    ("other-motor-cycle-scope-review", "cycles", "其他辅助动力车辆及边车范围待核",
     "核查 HS 87.11 同级残余项在 CPC 电驱动纳入句中的具体所指。", "8711.90", "motorcycles",
     (("49913", "C", "inclusion", None, "CPC 电驱动纳入句同时列出该残余项，具体纳入范围待核。"),)),
)


def build(assets, by_code, hs_review):
    wco = hs_review["scope_followup"]["wco_evidence"]
    evidence = {
        "wco-christmas-strings": pdf_excerpt(
            assets, "hs2022-chapter94", 4, 7, 10,
            ("Lighting strings of a kind used for Christmas trees", "9405.31", "9405.39"),
        ),
        "wco-other-electric-lighting": pdf_excerpt(
            assets, "hs2022-chapter94", 4, 11, 16,
            ("9405.41", "9405.42 -- Other, designed for use solely", "9405.49"),
        ),
        "wco-octopus": wco["HS:2022:0307:WCO:octopus"]["passages"][0],
        "wco-bituminous-coal": wco["HS:2022:27:WCO:subheading-note-2"]["passages"][0],
        "wco-coal-group": wco["HS:2022:2701:WCO:unagglomerated-coal"]["passages"][0],
        "wco-motorcycles-heading": wco["HS:2022:8711:WCO:heading"]["passages"][0],
        "wco-motorcycles": wco["HS:2022:8711:WCO:heading"]["passages"][1],
        "wco-octopus-powders": wco["HS:2022:03:WCO:chapter-note-3"]["passages"][0],
        "unsd-octopus-corrections": hs_review["scope_followup"]["corrigendum_audit"]["evidence"][0],
    }
    supplement = {
        "octopus": ["wco-octopus-powders", "unsd-octopus-corrections"],
        "bituminous-coal": ["wco-coal-group"],
        "motorcycles": ["wco-motorcycles-heading"],
    }
    hs_ids = {node["id"] for node in hs_review["hs_structure"]["nodes"]}
    references = {ref["id"]: ref for ref in hs_review["official_note_references"]}
    nodes, bindings, source_index = [], {}, {}

    def add_node(code, parent, label, scope, status):
        node = {
            "id": stable_id("concept", SCHEME + ":" + code), "code": code, "label": label,
            "parents": [parent] if parent else [], "scope": scope, "status": status, "binding_ids": [],
        }
        nodes.append(node)
        return node

    def bind(node, source_id, relation, reason, evidence_ids, clause_id=None):
        binding_id = stable_id("mapping", node["id"] + ":" + source_id)
        if binding_id in bindings:
            raise ValueError(f"duplicate Atlas goods binding: {binding_id}")
        bindings[binding_id] = {
            "id": binding_id, "concept_id": node["id"], "source_id": source_id,
            "status": "reviewed" if relation else "pending", "relation": relation, "reason": reason,
            "evidence_ids": evidence_ids, "source_clause_id": clause_id,
        }
        node["binding_ids"].append(binding_id)
        source_index.setdefault(source_id, []).append(binding_id)

    for code, parent, label, scope in NAVIGATION:
        add_node(code, parent, label, scope, "navigation")
    for code, parent, label, scope, hs_code, passage, cpc_bindings in LEAVES:
        reviewed = all(relation for _, _, _, relation, _ in cpc_bindings)
        node = add_node(code, parent, label, scope, "reviewed" if reviewed else "pending")
        hs_id = "HS:2022:" + hs_code
        proof = ["wco-" + passage, *supplement.get(passage, [])]
        if hs_id not in hs_ids or hs_code not in evidence[proof[0]]["text"]:
            raise ValueError(f"Atlas goods HS anchor is missing: {hs_id}")
        bind(node, hs_id, "exact" if reviewed else None,
             "Atlas 样本范围取自该 WCO 子目及上级分组。" if reviewed else "此 HS 子目为范围核查证据。",
             proof)
        for cpc_code, column, kind, relation, reason in cpc_bindings:
            cpc_id = by_code[cpc_code]["id"]
            ref_id = f"{cpc_id}:HS2022:{column}:1"
            ref = references[ref_id]
            if ref["kind"] != kind or (
                hs_id not in ref["target_ids"] and (relation or ref.get("review", {}).get("candidate_hs_id") != hs_id)
            ):
                raise ValueError(f"Atlas goods binding is missing its CPC clause: {ref_id} -> {hs_id}")
            evidence[ref_id] = {
                **hs_review["workbook"],
                **{key: ref[key] for key in ("sheet", "row", "column", "line", "kind", "text_sha256")},
            }
            bind(node, cpc_id, relation, reason, [ref_id, *proof], ref_id)

    if "not solely for LED light sources" not in by_code["46539"]["label"]:
        raise ValueError("CPC 46539 title changed; re-evaluate the LED scope conflict")
    quality = qa(nodes)
    if any(quality[key] for key in ("duplicate_codes", "orphan_parents", "self_links", "cycles")):
        raise ValueError("invalid Atlas trade-goods hierarchy")
    return {
        "scheme_id": SCHEME, "classification_object": "traded goods",
        "binding_direction": "Atlas to source", "source_editions": ["CPC:3.0", "HS:2022"],
        "nodes": nodes, "bindings": bindings, "source_index": source_index,
        "evidence": {key: {field: value for field, value in record.items() if field != "text"}
                     for key, record in evidence.items()},
        "summary": {
            "hierarchy": quality, "node_status": dict(Counter(node["status"] for node in nodes)),
            "binding_status": dict(Counter(item["status"] for item in bindings.values())),
            "reviewed_relations": dict(Counter(item["relation"] for item in bindings.values() if item["relation"])),
            "source_nodes": len(source_index), "evidence_records": len(evidence),
        },
    }
