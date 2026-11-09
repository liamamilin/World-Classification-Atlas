# CPC 46531 灯具范围与 LED 光源归属核查

2026-11-09 核对 HS 2022 `9405.19`、`9405.29`、`8539.51`、`8539.52` 的范围及对应。来源注册表的「产品与服务」可进入 Atlas 照明分支。四个商品范围都可回查 HS 子目和相关 CPC 条目，HS 页另列逐条 WCO 版本对应与 UNSD 旧表。 [机器可读目录](../data/atlas/products/trade-goods-directory.json)

## 9405.19、9405.29 与 46531

| HS 2022 | HS 范围 | CPC 3.0 标题范围核查 |
| --- | --- | --- |
| `9405.19` | 枝形吊灯和其他天花板或墙壁电灯具中的非 LED 专用残余项。上级分组排除公共开放场所或道路用灯具。 | `46531` 的天花板或墙壁灯具部分有相同场所例外，标题没有 LED 专用限制，范围较宽。 |
| `9405.29` | 台灯、书桌灯、床头灯及落地电灯具中的非 LED 专用残余项。 | `46531` 标题列举同样的灯具类型，未限定光源设计，范围较宽。 |

WCO 第 94 章的 `9405.11` 和 `9405.21` 分别列出两组的 LED 专用项，CPC `46533` 的定义明确引用这两码。CPC `46531` 还列便携灯、非电气灯具和发光标牌。它在工作簿 `CPC3!B2482`、说明 PDF 物理第 253 页和在线详情均仅有标题。Atlas 的两条 `source_broader` 记录标明依据为当前标题，现行具体归属保留待核。 [CPC 46531](https://unstats.un.org/unsd/classifications/Econ/Structure/Detail/EN/2100/46531) · [CPC 46533](https://unstats.un.org/unsd/classifications/Econ/Structure/Detail/EN/2100/46533) · [WCO 第 94 章第 3–4 页](https://www.wcoomd.org/-/media/wco/public/global/pdf/topics/nomenclature/instruments-and-tools/hs-nomenclature-2022/2022/2094_2022e.pdf?la=en#page=3)

WCO 表 I 对 `9405.19`、`9405.29` 分别列 `ex9405.10`、`ex9405.20`。表 II 将两个旧子目各拆到相应的 LED 专用项、残余项和部分 `8539.51`。UNSD 历史 CSV 第 5727、5728 行分别把两个旧码连到 CPC 2.1 `46531`，两行的 HS partial 为 `0`，CPC partial 为 `1`。 [WCO 表 I 第 33 页](https://www.wcoomd.org/-/media/wco/public/global/pdf/topics/nomenclature/instruments-and-tools/hs-nomenclature-2022/table-i_en.pdf?la=en#page=33) · [WCO 表 II 第 23 页](https://www.wcoomd.org/-/media/wco/public/global/pdf/topics/nomenclature/instruments-and-tools/hs-nomenclature-2022/table-ii_en.pdf?la=en#page=23) · [UNSD 历史对应 CSV](https://unstats.un.org/unsd/classifications/Econ/tables/CPC/CPCv21_HS2017/CPC21-HS2017.csv)

## 8539.51 模块与 8539.52 灯

HS 2022 第 85 章章注 11 以便于装卸、同时建立机械和电气接触的灯头区分两类光源。`8539.51` 的模块包含 LED、电路及相关部件，没有这种灯头。`8539.52` 的灯含一个或多个 LED 模块及相关部件，并有这种灯头。Atlas 新增带灯头的 LED 光源灯，与模块独立编目。CPC `46533` 的对象是面向 LED 光源设计的灯具。 [WCO 第 85 章章注第 2 页](https://www.wcoomd.org/-/media/wco/public/global/pdf/topics/nomenclature/instruments-and-tools/hs-nomenclature-2022/2022/1685_2022e.pdf?la=en#page=2) · [子目第 16 页](https://www.wcoomd.org/-/media/wco/public/global/pdf/topics/nomenclature/instruments-and-tools/hs-nomenclature-2022/2022/1685_2022e.pdf?la=en#page=16)

| HS 2022 | 历史证据 | 现行 CPC 3.0 状态 |
| --- | --- | --- |
| `8539.51` 模块 | 表 I 第 27 页列六个旧码的部分范围。表 II 对这些旧码均标 `ex8539.51`。历史 CSV 中涉及 CPC 2.1 的 `46541`、`46939`、`46531`、`46532`、`46539`。 | `46939` 只保留为部分范围候选，依据是旧 `8543.70` 的一部分转入，且旧表第 5303 行把该旧码列到 CPC 2.1 `46939`。 |
| `8539.52` 灯 | 表 I 第 27 页第 48 行、表 II 第 20 页第 5 行均列旧 `8539.50` 与新 `8539.52`，两侧均无 `ex`。旧 CSV 第 5274 行把旧码连到 CPC 2.1 `46939`，HS partial 为 `0`，CPC partial 为 `1`。 | 现行 `46939` 保留待核候选，标题是其他电气设备，未点名 LED 灯。 |

CPC 3.0 `46939` 和 `46510` 的工作簿说明单元格为空，PDF 第 254、252 页和在线详情仅列标题。`46510` 的标题列灯丝灯、放电灯及弧光灯。重新下载的 UNSD 工作簿和公开对应目录与锁定哈希一致，现行官方引用中未见这四个 HS 代码的解析目标，公开目录仍未列完整 CPC 3.0／HS 2022 对应表。 [CPC 46939](https://unstats.un.org/unsd/classifications/Econ/Structure/Detail/EN/2100/46939) · [CPC 46510](https://unstats.un.org/unsd/classifications/Econ/Structure/Detail/EN/2100/46510) · [现行说明工作簿](https://unstats.un.org/unsd/classifications/Econ/Download/In%20Text/CPC_Ver_3.0_Exp_Notes_30Jun2025.xlsx) · [UNSD 对应目录](https://unstats.un.org/unsd/classifications/Econ/CPC#corresp-cpc)

## 覆盖与复现

贸易商品样板共 23 个节点、22 条父子边、4 层。8 个导航节点、10 个已审商品范围和 5 个待核范围对应 24 个来源节点、34 条核查记录及 48 项证据。20 条已审记录含 11 条范围等价、7 条来源范围较宽及 2 条排除，另有 14 条待核绑定。两条新增的标题范围记录另带归属待核状态。四个核查范围合计有 9 条历史路径，包含既有的 `9405.40` 到 `ex8539.51`。原有 22 个节点 ID、29 个绑定 ID 和 69 条官方引用均通过基线对比。 [构建报告](../data/reports/cpc-offline.json)

首次复现先补齐前轮 26 份锁定资料，再采集三个新增 UNSD 页面。原始 HTML 在再分发许可确认前供本地查阅，仓库保存采集回执、哈希和证据定位。 [前轮采集入口](26-ATLAS-LIGHTING-HS-SPLIT.md#复现与验收) · [本轮采集回执](../data/acquisition/20261109T122048216815Z-562c941f.json) · [锁文件](../data/resources.lock.json)

```sh
python3 -m atlas_sources collect --resource cpc3-detail-46531-20261109 \
  --resource cpc3-detail-46939-20261109 --resource cpc3-detail-46510-20261109
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

Chrome 156.0.8078.80 在断网的 `file://` 会话中通过四个案例的 Atlas 与 CPC、HS 双向回查，以及模块和灯之间的互相回查。浏览器打开三个新增在线快照、CPC 原始 PDF、WCO 章注及两份版本对应表，并下载原始工作簿和历史 CSV。脚本核对原件 SHA-256、34 条 Atlas 绑定和 184 条现行官方引用回查路径，验证三份产物在干净目录复建后逐字节一致。100 项单测及 ISIC、家具 Chrome 回归通过。本轮登记的采集、构建和验收均成功。 [Chrome 验收脚本](../scripts/check_cpc_browser.js)
