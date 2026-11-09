# CPC 3.0 与 HS 2022 对应证据及离线复查

当前离线构建的完整采集清单见 [HS 2022 结构与双向回查](22-HS2022-STRUCTURE-AND-CPC-REFERENCES.md)。

## 发布范围

2026-11-09 核查 UNSD 的 CPC 下载页及经济分类总目录。锁定 CPC 页的 `corresp-cpc` 表，实测有 43 个链接，CPC 列到 2.1、HS 行到 2017，含可下载的 CPC 2.1／HS 2017 原表。该目录未找到完整 CPC 3.0／HS 2022 对应表。UNSD 2026 年 5 月培训资料物理第 46 页将该表列为进行中。这个缺口限于已核查的发布入口。 [CPC 下载页](https://unstats.un.org/unsd/classifications/Econ/CPC) · [经济分类总目录](https://unstats.un.org/unsd/classifications/Econ/) · [UNSD 培训原件](https://unstats.un.org/unsd/classifications/Workshops/AddisAbaba2026/Session4-Introduction-to-the-CPC-Ver-3-0.pdf#page=46)

UNSD 2025-06-30 的 CPC 3.0 说明工作簿有 4,586 个代码行，代码顺序与结构 CSV 一致。工作簿没有独立的 HS 对应栏，说明中的 69 条明确 HS 2022 引用分布于 64 个 CPC 节点，包括 60 条定义、7 条纳入和 2 条排除。页面保留原句、单元格及句行，公开 JSON 保留原码、代码写法、定位和文本哈希。省写的子目后缀、范围及其他原有写法按原件保留，未将每个记法展开成一条等价边。Chrome 正向对照为 `CPC:3.0:32193` 在 `CPC3!C1289` 引用 HS 2022 品目 `4818`，另核查 `46532` 引用 `9405.39` 作定义、排除 `9405.31` 的方向。 [官方工作簿](https://unstats.un.org/unsd/classifications/Econ/Download/In%20Text/CPC_Ver_3.0_Exp_Notes_30Jun2025.xlsx) · [机器可读报告](../data/reports/cpc-offline.json)

## 逐项范围结论

| 研究范围 | CPC 3.0 证据与状态 | HS 2022 证据 |
| --- | --- | --- |
| 简单纺织防护口罩 | `48160` 的标题排除同时无机械部件和可更换滤芯的防护口罩（CPC PDF 第 264 页）。`27190` 是有旧版依据的候选，当前说明表 `CPC3!1058` 的纳入和排除栏为空。保留归属待核。 | WCO／WHO 指南第 3 页将该类纺织口罩列在 `6307.90`，包括所列非织造、外科和 N95 示例。带机械部件或可更换滤芯的防毒面具另列 `9020.00`。 |
| 纸或纤维素口罩 | `48160` 的排除原文没有指定材料。当前 `32193` 的官方说明明确引用 HS 品目 `4818`，未单列纸口罩。页面可沿品目与子目核查两份证据。 | 指南第 3 页称多数国家归入 `4818.90`，有疑义时向有关海关确认。 |
| 碳纤维本体、织物和其他非电气用制品 | `37990` 标题给出非电气用石墨或其他碳制品的宽泛范围（CPC PDF 第 187 页）。`CPC3!1741` 没有具体说明或 HS 2022 引用，三个具体形态各自待核。 | WCO 第 68 章第 4 页分别列 `6815.11` 本体、`6815.12` 织物、`6815.13` 其他碳纤维制品。相同非电气用组的其他项为 `6815.19`。 |
| 电气用制品和碳纤维增强加工 | `46950` 标题限电气用途（CPC PDF 第 254 页），旧表列 `8545` 下的子目，当前具体制品对应待核。`89200` 正文涵盖可采用碳纤维增强的受托塑料件制造服务（第 487 页），成品归属待核。 | WCO 的 `6815.1` 范围以非电气用途区分。服务保留独立 CPC 记录。 |

口罩指南由 WCO 和 WHO 联合编制，所列商品为参考示例。CPC 是产品与服务目录，HS 是贸易商品目录，ISIC 的经济活动另有独立入口。 [WCO／WHO 指南](https://www.wcoomd.org/-/media/wco/public/global/pdf/topics/nomenclature/covid_19/hs-classification-reference_edition-3_en.pdf?la=pt-PT#page=3) · [WCO HS 2022 第 68 章](https://www.wcoomd.org/-/media/wco/public/global/pdf/topics/nomenclature/instruments-and-tools/hs-nomenclature-2022/2022/1368_2022e.pdf?la=en#page=4) · [UNSD CPC 3.0 说明 PDF](https://unstats.un.org/unsd/classifications/Econ/Download/In%20Text/CPC_Ver_3.0_Exp_Notes_30Jun2025.pdf)

## 历史原表与部分对应

- UNSD 的 CPC 2.1／HS 2017 CSV 实测 5,843 个代码对，页面逐条列出 19 个重点历史行，并另在报告保留 `32193` 的一个纸制品历史行。保留每行 `HS partial` 和 `CPC partial` 原值。按发布者说明，`1` 表示该侧代码对应对侧多项，`0` 表示单项。举例，`6307.90 ↔ 27190`、`6815.10 ↔ 37990` 和 `6815.99 ↔ 37990` 均为 HS 标记 `0`、CPC 标记 `1`。 [CSV 原件](https://unstats.un.org/unsd/classifications/Econ/tables/CPC/CPCv21_HS2017/CPC21-HS2017.csv) · [UNSD 对应表方法说明](https://unstats.un.org/unsd/classifications/Econ/tables/CPC/CPCv21_HS2017/Technical_note_CPC21-HS2017.pdf)
- WCO 表 I 第 17 页的代码列从 2022 指向 2017。`6815.11`、`6815.12`、`6815.13` 均指向 `ex6815.99`，`6815.19` 指向 `6815.10`。共用备注用 `6815.10` 概述拆分，范围说明和逐行代码分别保留。表 II 第 11 页的反向列显示旧 `6815.99` 包含上述三个新子目，旧 `6815.10` 指向新 `6815.19`。四对代码在两张原表中均核对到，三行保留表 I 的旧子目部分对应。WCO 将这两张表用于实施参考。历史关系不通过版次链生成当前 CPC 3.0 边。 [表 I](https://www.wcoomd.org/-/media/wco/public/global/pdf/topics/nomenclature/instruments-and-tools/hs-nomenclature-2022/table-i_en.pdf?la=en#page=17) · [表 II](https://www.wcoomd.org/-/media/wco/public/global/pdf/topics/nomenclature/instruments-and-tools/hs-nomenclature-2022/table-ii_en.pdf?la=en#page=11) · [WCO 表说明](https://www.wcoomd.org/en/topics/nomenclature/instrument-and-tools/hs-nomenclature-2022-edition/correlation-tables-hs-2017-2022.aspx?p=1)

## 采集与复现

本次新增 8 份锁定原件，实测均下载成功。CPC 构建共使用 10 个原件，包括前次的 CPC 结构 CSV 和说明 PDF。原始字节及含条款原文的浏览页留在 `data/local/`。Git 保存 SHA-256、采集回执、原码、定位与研究结论。WCO 版权所有，UNSD 原件的公开再分发权待核。 [采集资源登记](../data/registry/resources.json) · [锁文件](../data/resources.lock.json) · [WCO 版权条款](https://www.wcoomd.org/en/copyright.aspx)

首次缺少本地快照时联网执行下列采集命令。如果发布者更新下载字节，采集器会报告漂移并保留旧锁。复现这次结果需使用已保存的原始快照。后续构建需要 Python 3、Poppler 的 `pdftotext`、Node.js 与 Chrome。可用 `ATLAS_CHROME` 指定 Chrome 路径。

```sh
python3 -m atlas_sources collect \
  --resource cpc3-structure \
  --resource cpc3-notes-20250630 \
  --resource cpc3-notes-xlsx-20250630 \
  --resource cpc3-correspondence-listing-20261109 \
  --resource cpc3-hs2022-status-202605 \
  --resource cpc21-hs2017-unsd-correspondence \
  --resource hs2022-chapter68 \
  --resource hs2022-wco-who-medical-supplies \
  --resource hs2022-to-hs2017-wco-table-i \
  --resource hs2017-to-hs2022-wco-table-ii
```

```sh
python3 -m atlas_sources validate
python3 -m atlas_sources cpc
python3 -m atlas_sources report
python3 -m unittest discover -s tests -v
node scripts/check_cpc_browser.js
node scripts/check_economy_browser.js
node scripts/check_furniture_browser.js
open data/reports/registry.html
```

Chrome 156.0.8078.80 在独立配置、主页面离线和 HTTP(S) 请求阻断下，从「产品与服务」进入 CPC，点击口罩和碳纤维的两向回查并返回同一注册表筛选。浏览器打开 UNSD 发布页存档的对应表锚点、培训 PDF 第 46 页、指南第 3 页、HS 税则第 4 页、WCO 表 I 第 17 页与表 II 第 11 页。CPC 说明 PDF 的八处原有页定位通过。下载的工作簿及两个 CSV 和打开的原件均与锁文件 SHA-256 核对。首次把本地 HTML 存档作为下载等待时超时，改为直接打开 HTML 原件和表锚点后通过。仅用锁定输入在临时目录重建，页面及报告 2/2 逐字节一致。95 项 Python 单测及 ISIC、家具浏览回归通过。 [Chrome 验收脚本](../scripts/check_cpc_browser.js)
