# 贸易商品照明分支范围核查

本文记录该轮照明扩充的实测。最新目录覆盖和采集命令见 HS 版本拆分复核。 [当前目录与复现](26-ATLAS-LIGHTING-HS-SPLIT.md)

2026-11-09 核对 CPC 3.0 和 HS 2022。照明分支新增天花板或墙壁电灯具、台式及落地电灯具两个导航节点，以及两个已审商品范围和一个待核候选。可从来源注册表的「产品与服务」进入 Atlas 贸易商品目录。 [机器可读目录及逐条证据](../data/atlas/products/trade-goods-directory.json)

## 46539 的原文冲突

CPC 结构 CSV 第 2485 行和说明 PDF 物理第 253 页的标题均限定为非 LED 专用。工作簿 `CPC3!C2485` 的定义句却引用 `9405.42`，`D2485` 排除 `9405.41`。PDF 和本次采集的 UNSD 在线条目保留同样的定义及排除。注册表已锁定在线条目的 38,486 字节原响应、URL 和 SHA-256。 [UNSD 在线条目](https://unstats.un.org/unsd/classifications/Econ/Structure/Detail/EN/2100/46539) · [说明 PDF 第 253 页](https://unstats.un.org/unsd/classifications/Econ/Download/In%20Text/CPC_Ver_3.0_Exp_Notes_30Jun2025.pdf#page=253) · [工作簿](https://unstats.un.org/unsd/classifications/Econ/Download/In%20Text/CPC_Ver_3.0_Exp_Notes_30Jun2025.xlsx) · [采集回执](../data/acquisition/20261109T115550046878Z-2a96da55.json)

WCO 第 94 章物理第 4 页第 11–16 行列出「其他电灯及灯具」分组。`9405.41` 是光伏 LED 专用灯具，`9405.42` 是同组的其他 LED 专用灯具，`9405.49` 是同组残余子目。CPC 标题的「非 LED 专用」限定的是设计用途，可以包括兼容 LED 的灯具。Atlas 将 `9405.42` 的官方引用与范围冲突分开记录。以 CPC 标题和 WCO 同组残余范围支持的 `9405.49` 单列待核，从 Atlas 回查 CPC 标题和 HS 子目，两侧绑定的关系字段均为空。 [WCO 第 94 章第 4 页](https://www.wcoomd.org/-/media/wco/public/global/pdf/topics/nomenclature/instruments-and-tools/hs-nomenclature-2022/2022/2094_2022e.pdf?la=en#page=4)

2026-11-09 保存的 UNSD 注册表响应筛选了 CPC、3.0、更正、全部日期。页面记录的更新日期为 2026-11-03。唯一结果 4379 更正的是 `03239` 的重复词。在该快照中未找到 `46539` 的更正；`9405.42` 的 CPC 归属和 `9405.49` 的现行 CPC 对应仍待发布者确认。公开对应入口的独立 CPC 3.0／HS 2022 完整表也仍待取得。 [UNSD 注册表](https://unstats.un.org/unsd/classifications/Econ/Registry) · [更正 4379](https://unstats.un.org/unsd/classifications/Econ/Registry/Detail/4379) · [对应表发布核查](21-CPC-HS2022-REVIEW.md)

## 新增已审范围

| Atlas 范围 | HS 2022 锚点 | CPC 3.0 依据 |
| --- | --- | --- |
| LED 专用天花板或墙壁电灯具 | `9405.11`。WCO 第 3 页第 37–42 行。上级分组排除公共开放场所及道路照明灯具。 | `46533` 的 `CPC3!C2484` 明列该子目；CPC 范围更宽。 |
| LED 专用台灯、书桌灯、床头灯及落地灯 | `9405.21`。WCO 第 4 页第 3–6 行。 | 同一原句的 `.21` 承接 `9405`；CPC 范围更宽。 |

CPC `46533` 的定义还列出 `9405.31` 和 `9405.41`，没有列出 `9405.42`。两个新增 Atlas 商品范围分别与各自的 HS 子目等价。既有 Atlas `9405.41` 仍可回查 `46539` 的排除原句及 `46533` 的定义原句。 [CPC 46533 在线说明](https://unstats.un.org/unsd/classifications/Econ/Structure/Detail/EN/2100/46533) · [WCO 第 94 章第 3–4 页](https://www.wcoomd.org/-/media/wco/public/global/pdf/topics/nomenclature/instruments-and-tools/hs-nomenclature-2022/2022/2094_2022e.pdf?la=en#page=3)

实测目录共 19 个节点、18 条父子边、4 层。8 个导航节点下有 6 个已审商品范围和 5 个待核范围。18 个来源节点对应 25 条核查记录和 24 个证据记录。14 条已审关系分为 7 条等价、5 条来源范围更宽及 2 条排除。另有 11 条待核。与上一提交逐条对比，14 个原有节点 ID、19 个原有绑定 ID 及其状态、69 条官方引用的原码、哈希、定位与目标列表均保留。 [构建报告](../data/reports/cpc-offline.json)

## 复现与验收

首次复现先按前次报告补齐 22 份锁定资料，再采集本轮新增的在线条目。在线页面的响应可能随发布更新而变化。已有锁值校验失败时需核对发布版本。UNSD 原始 HTML 的再分发许可待确认，WCO 原始 PDF 按本地查阅条件处理。仓库保存 Atlas 目录、逐条定位、采集回执和校验值。 [既有资料采集入口](23-CPC-HS-BOUNDARY-FOLLOWUP.md#复现与验收) · [锁文件](../data/resources.lock.json)

```sh
python3 -m atlas_sources collect --resource cpc3-detail-46539-20261109
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

Chrome 156.0.8078.80 在 `file://` 且网络禁用的会话中实际点击 Atlas 与 CPC、HS 双向入口，核对 `9405.11`、`9405.21`、`9405.42` 和 `9405.49`。浏览器打开 WCO PDF 第 3、4 页、CPC PDF 第 253 页、在线条目及更正筛选快照，并下载 CSV 和工作簿。脚本对文件及下载结果核对锁定哈希，检查全部 25 条 Atlas 记录和 184 条 CPC 官方引用回查路径。临时目录仅使用锁定原件重建，页面、机器可读目录和构建报告 3/3 逐字节一致。100 项单测以及 ISIC 和家具的 Chrome 回归均通过。本轮新增采集及专项构建均成功。 [Chrome 验收脚本](../scripts/check_cpc_browser.js)
