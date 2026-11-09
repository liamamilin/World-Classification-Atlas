# HS 2022 结构与 CPC 3.0 引用回查

当前构建的五项补充资源见 [范围复核与复现](23-CPC-HS-BOUNDARY-FOLLOWUP.md#复现与验收)。

2026-11-09 从 UNSD 的官方分类下载页取得多版 HS 代码工作簿，选用标注 `H6` 的 `HS22` 工作表。章、品目、子目的原码、原文标题、父码及行号取自该工作表。部的标题及章所属部取自 WCO 2022 年税则目录，每个部和章都可追溯到 PDF 页及行。原码保留前导零，六位子目另用带点形式显示并沿用已有 `HS:2022:6815.12` 等 ID。 [UNSD 发布入口](https://unstats.un.org/unsd/classifications/Econ/) · [UNSD 原始工作簿](https://unstats.un.org/unsd/classifications/Econ/download/In%20Text/HSCodeandDescription.xlsx) · [WCO 2022 税则目录](https://www.wcoomd.org/-/media/wco/public/global/pdf/topics/nomenclature/instruments-and-tools/hs-nomenclature-2022/2022/table-of-contents_2022e_rev.pdf?la=en)

| 层级 | 节点数 | 来源 |
| --- | ---: | --- |
| 部 | 21 | WCO 目录 |
| 章 | 96 | UNSD 代码及 WCO 目录归属 |
| 品目 | 1,228 | UNSD 工作表 |
| 六位子目 | 5,612 | UNSD 工作表 |

合计 6,957 个节点及 6,936 条父子边，无重复、孤儿或环。原工作表共 6,940 条数据行，其中 `TOTAL`、`99`、`9999`、`999999` 四条贸易统计汇总，报告保留原行号和父码。WCO 目录把 77、98、99 列为保留，税则树排除上述统计汇总。本次浏览层级为部、章、品目、六位子目，WCO 税则中的破折号分组和法律说明可查看相关原件。UN Comtrade 的查询 JSON 用于前期核查，正式采集使用 UNSD 目录直接提供的工作簿。 [WCO 发布说明](https://www.wcoomd.org/en/media/newsroom/2021/november/the-2022-edition-of-the-harmonized-system-nomenclature-is-now-available-online.aspx?p=1) · [UN Comtrade 使用条款](https://comtradeplus.un.org/en/license-agreement)

## 69 条官方说明引用

CPC 3.0 工作簿的 64 个条目包含 69 条 HS 2022 引用，分别为 60 条定义、7 条纳入和 2 条排除。复核了 157 段代码写法。68 条引用全部解析，另 1 条保留一个缺码和一个已核实子目。共建立 184 条从原句到现有 HS 节点的链接，涉及 181 个 HS 节点。链接包括 173 条定义、9 条纳入和 2 条排除。反向入口跳回同一原句，标签沿用 CPC 原句的方向。工作簿及 PDF 中的说明是引用依据，完整的版次对应表仍在已核查的公开目录中缺失。 [CPC 原始工作簿](https://unstats.un.org/unsd/classifications/Econ/Download/In%20Text/CPC_Ver_3.0_Exp_Notes_30Jun2025.xlsx) · [逐条机器可读报告](../data/reports/cpc-offline.json)

每条记录保存源版次、稳定引用 ID、工作表、单元格、单元格内行号、原始写法、原句 SHA-256、拆解结果和具体目标。省写后缀沿用本组的品目，保留章节前导零。破折号范围只收录端点之间实际存在的同品目子目，斜杠按原句并列读取。四位引用停在品目层。重点复核结果如下。

| 原句定位 | 核查结论 |
| --- | --- |
| `CPC3!C633`，`21267` | 工作簿与 CPC 说明 PDF 第 79 页都写 `0307.53`。HS 2022 工作表和 WCO 第 03 章第 11 页均无该码，后者列 `0307.52` 冷冻章鱼和 `0307.59` 其他。后者接通官方原句回查，前者单列 Atlas 待核候选。 |
| `CPC3!C435` 与 `C439`，`11012`、`11031` | 工作簿的烟煤与次烟煤均引用 `2701.12`。WCO 第 27 章第 1 页明确给出该子目的烟煤定义。两条原句均可回查，CPC 范围分界待核。 |
| `CPC3!C1542–C1543`，`35272`、`35273` | `3002.90` 是 HS 残余子目，具体范围待核。`3002.41-49` 实际有 `.41/.42/.49`，`3002.51/59` 为 `.51/.59`。WCO 第 30 章第 3 页核实五项。 |
| `CPC3!C2073`，`41609` | 在原句保留 `8105.30. 8108.30`，逐个回查两个废料子目。 |
| `CPC3!D2483`、`C2484`、`D2485` | `9405.11, .21, 31, 41` 中末两项按 `9405.31`、`9405.41` 回查。它们在 `46533` 是定义引用，在 `46532`、`46539` 分别是排除。 |
| `CPC3!C2739`，`49913` | 纳入句明确提到电驱动，WCO 第 87 章第 5 页列 `8711.60` 电驱动、`8711.90` 其他。两码保留原句回查，`8711.90` 的具体范围待核。 |

[WCO 第 03 章](https://www.wcoomd.org/-/media/wco/public/global/pdf/topics/nomenclature/instruments-and-tools/hs-nomenclature-2022/2022/0103_2022e.pdf?la=en#page=11) · [第 27 章](https://www.wcoomd.org/-/media/wco/public/global/pdf/topics/nomenclature/instruments-and-tools/hs-nomenclature-2022/2022/0527_2022e.pdf#page=1) · [第 30 章](https://www.wcoomd.org/-/media/wco/public/global/pdf/topics/nomenclature/instruments-and-tools/hs-nomenclature-2022/2022/0630_2022e.pdf?la=en#page=3) · [第 87 章](https://www.wcoomd.org/-/media/wco/public/global/pdf/topics/nomenclature/instruments-and-tools/hs-nomenclature-2022/2022/1787_2022e.pdf?la=en#page=5) · [第 94 章](https://www.wcoomd.org/-/media/wco/public/global/pdf/topics/nomenclature/instruments-and-tools/hs-nomenclature-2022/2022/2094_2022e.pdf?la=en#page=4)

口罩和碳纤维继续通过独立的 Atlas 范围核查回链。WCO 参考指南、CPC 2.1／HS 2017 的双侧 `partial` 和 WCO 两版 HS 表的 `ex` 各自保留版次和出处。它们未生成 CPC 3.0 的官方说明回链。 [前次范围核查](21-CPC-HS2022-REVIEW.md)

## 复现和验收

已持有前次 10 份 CPC 资料时，先联网补齐以下七份。全新工作区还需运行前次报告的十份资源采集命令。原始工作簿、WCO 税则 PDF 及含原文的离线页留在本地，Git 保存采集回执、锁定哈希、代码、定位和核查结果。 [既有十份资源的采集命令](21-CPC-HS2022-REVIEW.md#采集与复现) · [资源清单](../data/registry/resources.json) · [锁文件](../data/resources.lock.json)

```sh
python3 -m atlas_sources collect \
  --resource hs2022-unsd-structure --resource hs2022-wco-contents \
  --resource hs2022-chapter03 --resource hs2022-chapter27 --resource hs2022-chapter30 \
  --resource hs2022-chapter87 --resource hs2022-chapter94
```

```sh
python3 -m atlas_sources validate
python3 -m atlas_sources cpc
python3 -m atlas_sources report
python3 -m unittest discover -s tests -v
node scripts/check_cpc_browser.js
open data/reports/registry.html
```

Chrome 156.0.8078.80 在独立配置、网络离线和 HTTP(S) 阻断下打开两个注册表入口。实测四级结构、无点代码搜索、精确原句回查、章鱼待核候选、灯具排除和煤炭共享引用。七个新原件以及十个既有原件均经浏览器打开或下载，按锁文件核对 SHA-256。Chrome 内逐条检查 69 条原句及全部 184 条正反向链接的渲染，代表性路径另作实际点击。首轮批量快速改写同页地址后出现定位失败，改用每条独立渲染并保留实际点击测试后通过。临时目录只复制锁定原件和登记资料，页面及报告 2/2 逐字节一致。99 项 Python 单测通过，ISIC 和家具的 Chrome 回归均通过。 [浏览器验收脚本](../scripts/check_cpc_browser.js)
