# HS 9405.40 历史拆分与照明现行对应复核

本文记录该轮历史拆分实测。最新覆盖和完整采集命令见灯具与 LED 光源核查。 [当前目录与复现](27-ATLAS-LIGHTING-FIXTURES-LED.md)

2026-11-09 从来源注册表的「产品与服务」进入统一离线浏览。Atlas 照明分支与 CPC 3.0、HS 2022 源节点可双向回查。HS 2017 `9405.40` 有单独的历史证据页和稳定 ID，四个 HS 2022 去向都可回到该页。 [目录与逐条证据](../data/atlas/products/trade-goods-directory.json)

## WCO 两表的原码

HS 2017 第 94 章物理第 3 页第 24 行将 `9405.40` 列为其他电灯及灯具。表 I 从 HS 2022 回看 2017，表 II 从 HS 2017 查往 2022。下表保留每侧原有 `ex`。 [HS 2017 第 94 章](https://www.wcoomd.org/-/media/wco/public/global/pdf/topics/nomenclature/instruments-and-tools/hs-nomenclature-2017/2017/2094_2017e.pdf?la=en#page=3) · [WCO 表 I](https://www.wcoomd.org/-/media/wco/public/global/pdf/topics/nomenclature/instruments-and-tools/hs-nomenclature-2022/table-i_en.pdf?la=en) · [WCO 表 II](https://www.wcoomd.org/-/media/wco/public/global/pdf/topics/nomenclature/instruments-and-tools/hs-nomenclature-2022/table-ii_en.pdf?la=en#page=23)

| HS 2022 商品范围 | 表 I 的 2022 → 2017 原码 | 表 II 的 2017 → 2022 原码 |
| --- | --- | --- |
| LED 光源模块的一部分 | `8539.51 → ex9405.40`，第 27 页第 46 行 | `9405.40 → ex8539.51`，第 23 页第 42 行 |
| 光伏 LED 专用电灯具 | `9405.41 → ex9405.40`，第 33 页第 18 行 | `9405.40 → 9405.41`，第 23 页第 43 行 |
| 同组其他 LED 专用电灯具 | `9405.42 → ex9405.40`，第 33 页第 20 行 | `9405.40 → 9405.42`，第 23 页第 44 行 |
| 同组残余电灯具 | `9405.49 → ex9405.40`，第 33 页第 22 行 | `9405.40 → 9405.49`，第 23 页第 45 行 |

表 I 第 27 页对 `8539.51` 共列六个旧码部分，除 `ex9405.40` 外，还有 `ex8539.90`、`ex8543.70`、`ex9405.10`、`ex9405.20`、`ex9405.30`。UNSD 历史 CSV 第 5730 行连接 HS 2017 `9405.40` 与 CPC 2.1 `46539`，两侧 partial 原值均为 `0`。该行只在历史证据页展示；WCO 拆分和现行 CPC 官方引用分别存储。 [WCO 表 I 第 27 页](https://www.wcoomd.org/-/media/wco/public/global/pdf/topics/nomenclature/instruments-and-tools/hs-nomenclature-2022/table-i_en.pdf?la=en#page=27) · [UNSD 历史对应 CSV](https://unstats.un.org/unsd/classifications/Econ/tables/CPC/CPCv21_HS2017/CPC21-HS2017.csv)

## 现行 CPC 说明和公开发布证据

| 待核项 | 核查结果 |
| --- | --- |
| `9405.42` 与 CPC 3.0 `46533` | 标题范围都指 LED 专用灯具。UNSD 在线详情、说明 PDF 第 253 页和 `CPC3!C2484` 的定义句均只列 `.11`、`.21`、`.31`、`.41`。Atlas 保留标题范围候选，可回查 CPC 标题和证据。 |
| `9405.42` 与 CPC 3.0 `46539` | 在线详情、PDF 和 `CPC3!C2485` 继续引用 `.42`，标题却限定非 LED 专用。`D2485` 仍排除 `.41`。官方原句回查保留，范围标注待核。 |
| `9405.49` 与 CPC 3.0 `46539` | WCO 同组残余范围支持保留候选。已核查的 CPC 定义和排除原句未列 `.49`，公开更正记录未见替换为该码的决定。 |

[UNSD 46533](https://unstats.un.org/unsd/classifications/Econ/Structure/Detail/EN/2100/46533) · [UNSD 46539](https://unstats.un.org/unsd/classifications/Econ/Structure/Detail/EN/2100/46539) · [CPC 说明 PDF 第 253 页](https://unstats.un.org/unsd/classifications/Econ/Download/In%20Text/CPC_Ver_3.0_Exp_Notes_30Jun2025.pdf#page=253) · [CPC 说明工作簿](https://unstats.un.org/unsd/classifications/Econ/Download/In%20Text/CPC_Ver_3.0_Exp_Notes_30Jun2025.xlsx)

本轮重取 UNSD CPC 发布目录、`46539` 在线详情和公开注册表筛选响应，三个 SHA-256 均与锁文件一致。更正检索为 CPC、3.0、更正、全部日期，页面最近更新为 2026-11-03，唯一结果仍是更正 `03239` 重复词的 4379。公开对应目录仍未列完整 CPC 3.0／HS 2022 表，2026 年 5 月培训材料第 46 页记为进行中。两项现行归属仍待发布者确认。 [UNSD 对应目录](https://unstats.un.org/unsd/classifications/Econ/CPC#corresp-cpc) · [更正注册表](https://unstats.un.org/unsd/classifications/Econ/Registry) · [更正 4379](https://unstats.un.org/unsd/classifications/Econ/Registry/Detail/4379) · [培训材料第 46 页](https://unstats.un.org/unsd/classifications/Workshops/AddisAbaba2026/Session4-Introduction-to-the-CPC-Ver-3-0.pdf#page=46)

## 新增已审范围与覆盖

新增 HS `9405.19` 的其他天花板或墙壁电灯具、`9405.29` 的其他台式及落地电灯具，以及 `8539.51` 的 LED 光源模块。前两项取自 WCO 第 94 章同组残余范围。LED 模块按第 85 章第 16 页子目及第 2 页章注 11 审定，章注区分模块与具备便捷装卸和电气接触功能的带灯头 LED 灯。三个新增范围均明确标示 CPC 对应尚未审定。 [WCO 第 94 章](https://www.wcoomd.org/-/media/wco/public/global/pdf/topics/nomenclature/instruments-and-tools/hs-nomenclature-2022/2022/2094_2022e.pdf?la=en#page=3) · [WCO 第 85 章章注](https://www.wcoomd.org/-/media/wco/public/global/pdf/topics/nomenclature/instruments-and-tools/hs-nomenclature-2022/2022/1685_2022e.pdf?la=en#page=2)

贸易商品样板现有 22 个节点、21 条父子边和 4 层。9 个已审范围、5 个待核范围和 8 个导航节点共关联 21 个来源节点，提供 29 条逐条核查记录和 34 项证据定位。17 条已审记录含 10 条等价、5 条来源更宽、2 条排除，另有 12 条待核。前轮 19 个节点 ID、25 个绑定 ID 及关系和状态均经逐条对比。69 条 CPC 官方引用和 184 条回查路径保持原样。 [构建报告](../data/reports/cpc-offline.json)

## 复现与验收

首次复现先采集前轮的 23 份资料，再下载本轮三个新原件。三份原件均采集成功。WCO PDF 供本地查阅，UNSD HTML 再分发条件待确认。仓库提交采集回执、哈希锁、证据定位、Atlas 目录和可复现代码。 [前轮采集入口](25-ATLAS-LIGHTING-SCOPE.md#复现与验收) · [本轮采集回执](../data/acquisition/20261109T120603247145Z-7fc5b23d.json) · [锁文件](../data/resources.lock.json)

```sh
python3 -m atlas_sources collect --resource cpc3-detail-46533-20261109 \
  --resource hs2017-chapter94 --resource hs2022-chapter85
python3 -m atlas_sources validate
python3 -m atlas_sources verify
python3 -m atlas_sources cpc
python3 -m atlas_sources report
python3 -m unittest discover -s tests -v
node scripts/check_cpc_browser.js
node scripts/check_economy_browser.js
node scripts/check_furniture_browser.js
open data/reports/registry.html
```

Chrome 156.0.8078.80 使用网络禁用的 `file://` 会话，点击历史税则与四个去向的全部往返路径，打开两张 WCO 对应表、旧税则、HS 第 85 章税则和章注，下载旧 CSV 并校验锁定哈希。核对了 `.42` 与 `.49` 候选、三个新增范围的双向回查，以及全部 29 条 Atlas 记录和 184 条官方引用路径。首次验收发现历史 CSV 下载按钮缺少标识，修复后重跑通过。干净目录重建的三个产物逐字节一致。100 项单测和 ISIC、家具 Chrome 回归通过。 [Chrome 验收脚本](../scripts/check_cpc_browser.js)
