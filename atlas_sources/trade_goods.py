"""Reviewed trade-goods sample built from pinned CPC clauses and WCO passages."""
from collections import Counter

from . import cpc_lighting
from .cpc_hs_followup import pdf_excerpt
from .isic import stable_id
from .normalize import qa

PUBLIC = "data/atlas/products/trade-goods-directory.json"
SCHEME = "urn:atlas:scheme:trade-goods"
NAVIGATION = (
    ("trade-goods", None, "贸易商品", "按商品形态、用途和工艺组织的 Atlas 样板。"),
    ("lighting", "trade-goods", "照明商品", "按用途和光源设计区分照明商品，保留各税则分组的范围。"),
    ("tree-lights", "lighting", "圣诞树用灯串", "按是否仅为 LED 光源设计分开。"),
    ("ceiling-wall-lights", "lighting", "天花板或墙壁电灯具", "该税则分组排除公共开放场所或道路照明灯具。"),
    ("table-floor-lights", "lighting", "台式及落地电灯具", "该税则分组涵盖台灯、书桌灯、床头灯及落地灯。"),
    ("seafood", "trade-goods", "水产商品", "按物种和加工形态组织，当前选取冷冻章鱼候选。"),
    ("coal", "trade-goods", "煤炭商品", "保留商品形态、煤种及判定口径的差异。"),
    ("cycles", "trade-goods", "摩托车及装辅助动力的脚踏车", "按驱动和边车范围组织有证据的样本。"),
)

# A leaf has a WCO anchor and may have CPC clause bindings or a separately marked title-based candidate.
# A missing relation marks a pending binding. Reviewed exclusions are kept separately from positive matches.
LEAVES = (
    ("tree-lights-led-only", "tree-lights", "LED 专用圣诞树灯串",
     "仅为 LED 光源设计的圣诞树用灯串。", "9405.31", "christmas-strings",
     (("46533", "C", "definition", "source_broader", "该 CPC 子类还涵盖其他 LED 专用灯具。"),
      ("46532", "D", "exclusion", "excluded", "CPC 排除句明确列出 9405.31。"))),
    ("tree-lights-other", "tree-lights", "其他圣诞树灯串",
     "圣诞树用灯串中，未限定为仅使用 LED 光源的部分。", "9405.39", "christmas-strings",
     (("46532", "C", "definition", "exact", "CPC 定义指向 9405.39，并明确排除同组 LED 专用灯串。"),)),
    ("ceiling-wall-led-only", "ceiling-wall-lights", "LED 专用天花板或墙壁电灯具",
     "仅为 LED 光源设计的枝形吊灯和其他天花板或墙壁电灯具。公共开放场所或道路照明灯具另有归类。",
     "9405.11", "ceiling-wall-lights",
     (("46533", "C", "definition", "source_broader", "CPC 定义明确列出 9405.11，还涵盖另外三个 LED 专用子目。"),)),
    ("ceiling-wall-other", "ceiling-wall-lights", "其他天花板或墙壁电灯具",
     "该组扣除 LED 专用灯具后的范围。上级分组排除公共开放场所或道路照明灯具。",
     "9405.19", "ceiling-wall-lights", ()),
    ("table-floor-led-only", "table-floor-lights", "LED 专用台灯、书桌灯、床头灯及落地灯",
     "仅为 LED 光源设计的台灯、书桌灯、床头灯及落地灯。", "9405.21", "table-floor-lights",
     (("46533", "C", "definition", "source_broader", "原句缩写 .21 承接 9405，CPC 定义还涵盖另外三个 LED 专用子目。"),)),
    ("table-floor-other", "table-floor-lights", "其他台灯、书桌灯、床头灯及落地灯",
     "该组扣除 LED 专用灯具后的范围。", "9405.29", "table-floor-lights", ()),
    ("other-photovoltaic-led", "lighting", "其他光伏 LED 专用电灯具",
     "归在其他电灯及灯具中的光伏产品，仅为 LED 光源设计。", "9405.41", "other-electric-lighting",
     (("46533", "C", "definition", "source_broader", "该 CPC 子类还涵盖其他用途的 LED 专用灯具。"),
      ("46539", "D", "exclusion", "excluded", "CPC 排除句明确列出 9405.41。"))),
    ("other-led-scope-review", "lighting", "其他 LED 专用电灯具对应待核",
     "核查 HS 所列的其他 LED 专用电灯具，与 CPC 原句所指范围的差异。", "9405.42", "other-electric-lighting",
     (("46539", "C", "definition", None, "CPC 标题限定非 LED 专用，所引的 9405.42 却明确限定 LED 专用。"),
      ("46533", "C", "title_candidate", None, "CPC 标题和 HS 子目均指 LED 专用灯具。CPC 的定义句只列 .11、.21、.31、.41，.42 的归属待核。"))),
    ("other-electric-lighting-residual-candidate", "lighting", "其他电灯具的非 LED 专用范围候选",
     "以 HS 其他电灯具分组中的残余子目为依据，核查其与 CPC 非 LED 专用标题的范围。",
     "9405.49", "other-electric-lighting",
     (("46539", "C", "title_candidate", None,
       "9405.49 扣除同组 9405.41 和 9405.42 后与 CPC 标题方向相符。CPC 定义原句引用 9405.42，具体对应待核。"),)),
    ("led-light-source-modules", "lighting", "LED 光源模块",
     "由 LED 和电路等构成的光源模块。按 HS 章注，模块没有便于在灯具中装卸并建立机械和电气接触的灯头。",
     "8539.51", "led-modules", ()),
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


def build(assets, by_code, hs_review, structure, notes):
    wco = hs_review["scope_followup"]["wco_evidence"]
    corrections = hs_review["scope_followup"]["corrigendum_audit"]
    references = {ref["id"]: ref for ref in hs_review["official_note_references"]}
    lighting, lighting_evidence = cpc_lighting.build(assets, by_code, hs_review, structure, notes, references)
    evidence = {
        **lighting_evidence,
        "wco-ceiling-wall-lights": pdf_excerpt(
            assets, "hs2022-chapter94", 3, 37, 42,
            ("ceiling or wall lighting fittings", "excluding those", "thoroughfares",
             "9405.11 -- Designed for use solely", "9405.19"),
        ),
        "wco-table-floor-lights": pdf_excerpt(
            assets, "hs2022-chapter94", 4, 3, 6,
            ("table, desk, bedside or floor-standing", "9405.21 -- Designed for use solely", "9405.29"),
        ),
        "wco-christmas-strings": pdf_excerpt(
            assets, "hs2022-chapter94", 4, 7, 10,
            ("Lighting strings of a kind used for Christmas trees", "9405.31", "9405.39"),
        ),
        "wco-other-electric-lighting": pdf_excerpt(
            assets, "hs2022-chapter94", 4, 11, 16,
            ("Other electric luminaires and lighting fittings", "9405.41 -- Photovoltaic",
             "9405.42 -- Other, designed for use solely", "9405.49 -- Other"),
        ),
        "wco-led-modules": pdf_excerpt(
            assets, cpc_lighting.MODULES_CHAPTER, 16, 10, 12,
            ("8539.51 -- Light-emitting diode (LED) modules", "8539.52 -- Light-emitting diode (LED) lamps"),
        ),
        "wco-led-source-note": pdf_excerpt(
            assets, cpc_lighting.MODULES_CHAPTER, 2, 28, 39,
            ("LED) light sources", "modules do not have a cap", "lamps have a cap"),
        ),
        "wco-octopus": wco["HS:2022:0307:WCO:octopus"]["passages"][0],
        "wco-bituminous-coal": wco["HS:2022:27:WCO:subheading-note-2"]["passages"][0],
        "wco-coal-group": wco["HS:2022:2701:WCO:unagglomerated-coal"]["passages"][0],
        "wco-motorcycles-heading": wco["HS:2022:8711:WCO:heading"]["passages"][0],
        "wco-motorcycles": wco["HS:2022:8711:WCO:heading"]["passages"][1],
        "wco-octopus-powders": wco["HS:2022:03:WCO:chapter-note-3"]["passages"][0],
        "unsd-octopus-corrections": corrections["evidence"][0],
    }
    supplement = {
        "led-modules": ["wco-led-source-note"],
        "octopus": ["wco-octopus-powders", "unsd-octopus-corrections"],
        "bituminous-coal": ["wco-coal-group"],
        "motorcycles": ["wco-motorcycles-heading"],
    }
    hs_ids = {node["id"] for node in hs_review["hs_structure"]["nodes"]}
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
        if not cpc_bindings:
            node["cpc_scope_status"] = "not_reviewed"
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
            title_candidate = kind == "title_candidate"
            if title_candidate:
                if relation or cpc_lighting.CANDIDATES.get(ref_id) != hs_id or hs_id in ref["target_ids"]:
                    raise ValueError(f"unexpected lighting title candidate: {ref_id} -> {hs_id}")
            elif ref["kind"] != kind or (
                hs_id not in ref["target_ids"] and (relation or ref.get("review", {}).get("candidate_hs_id") != hs_id)
            ):
                raise ValueError(f"Atlas goods binding is missing its CPC clause: {ref_id} -> {hs_id}")
            evidence[ref_id] = {
                **hs_review["workbook"],
                **{key: ref[key] for key in ("sheet", "row", "column", "line", "kind", "text_sha256")},
            }
            cpc_proof = [ref_id, *proof]
            if ref_id == cpc_lighting.LITERAL_CLAUSE or title_candidate:
                cpc_proof.extend([f"cpc-{cpc_code}-pdf", f"cpc-{cpc_code}-online",
                                  "unsd-cpc3-corrections", "unsd-cpc3-correspondence"])
            if ref_id == cpc_lighting.LITERAL_CLAUSE:
                cpc_proof.append("cpc-46539-title")
            bind(node, cpc_id, relation, reason, cpc_proof, None if title_candidate else ref_id)

    quality = qa(nodes)
    if any(quality[key] for key in ("duplicate_codes", "orphan_parents", "self_links", "cycles")):
        raise ValueError("invalid Atlas trade-goods hierarchy")
    return {
        "scheme_id": SCHEME, "classification_object": "traded goods",
        "binding_direction": "Atlas to source", "source_editions": ["CPC:3.0", "HS:2022"],
        "nodes": nodes, "bindings": bindings, "source_index": source_index,
        "lighting_review": lighting,
        "evidence": {key: {field: value for field, value in record.items() if field != "text"}
                     for key, record in evidence.items()},
        "summary": {
            "hierarchy": quality, "node_status": dict(Counter(node["status"] for node in nodes)),
            "binding_status": dict(Counter(item["status"] for item in bindings.values())),
            "reviewed_relations": dict(Counter(item["relation"] for item in bindings.values() if item["relation"])),
            "source_nodes": len(source_index), "evidence_records": len(evidence),
        },
    }
