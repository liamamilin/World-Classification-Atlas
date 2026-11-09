# Atlas 贸易商品自有目录样板

Atlas 样板将部分贸易商品按形态、用途和工艺组织为照明、水产、煤炭和摩托车分支。CPC 3.0 与 HS 2022 在同一离线页内独立浏览，Atlas 层级使用独立的 `urn:atlas:scheme:trade-goods` 和节点 ID。目录从注册表「产品与服务」进入，可按商品名称或所引原码检索。 [机器可读目录](../data/atlas/products/trade-goods-directory.json) · [CPC 3.0 原始工作簿](https://unstats.un.org/unsd/classifications/Econ/Download/In%20Text/CPC_Ver_3.0_Exp_Notes_30Jun2025.xlsx) · [WCO HS 2022 税则目录](https://www.wcoomd.org/en/topics/nomenclature/instrument-and-tools/hs-nomenclature-2022-edition/hs-nomenclature-2022-edition.aspx)

样板有 14 个节点、13 条父子边和 4 层。6 个节点用于导航，4 个叶节点的商品范围已审，4 个叶节点保留待核范围。15 个来源节点对应 19 条逐条核查记录，含 10 条已审记录及 9 条待核记录。已审记录含 5 条范围等价、3 条来源范围更宽和 2 条排除。待核记录的关系字段为空，保留原句、税则和待核理由。所有关系方向均为 Atlas 范围到来源。 [构建报告](../data/reports/cpc-offline.json)

| Atlas 范围 | 已审关系及边界 |
| --- | --- |
| LED 专用圣诞树灯串 | HS `9405.31` 与样本范围等价。CPC `46533` 定义句的范围更宽，`46532` 排除句明确列出该子目。 |
| 其他圣诞树灯串 | HS `9405.39` 及 CPC `46532` 的范围与此样本等价，均保留与 LED 专用灯串的分界。 |
| 其他光伏 LED 专用电灯具 | HS `9405.41` 与样本范围等价。CPC `46533` 范围更宽，`46539` 排除句明确列出该子目。 |
| 电动机驱动的摩托车及辅助动力脚踏车 | HS `8711.60` 与样本范围等价，CPC `49913` 明确纳入电驱动，子类还覆盖更宽的辅助动力和边车范围。 |

[WCO 第 94 章第 4 页](https://www.wcoomd.org/-/media/wco/public/global/pdf/topics/nomenclature/instruments-and-tools/hs-nomenclature-2022/2022/2094_2022e.pdf?la=en#page=4) · [UNSD CPC 照明设备](https://unstats.un.org/unsd/classifications/Econ/Structure/Detail/EN/2100/4653) · [WCO 第 87 章第 5 页](https://www.wcoomd.org/-/media/wco/public/global/pdf/topics/nomenclature/instruments-and-tools/hs-nomenclature-2022/2022/1787_2022e.pdf?la=en#page=5)

其他 LED 专用电灯具另列待核。CPC `46539` 标题限定非 LED 专用，定义句引用的 HS `9405.42` 却明列 LED 专用，双方原句和原码保留。冷冻章鱼 `0307.52`、两条煤炭说明共引 `2701.12` 及 `8711.90` 的纳入边界也各有待核叶节点。原始 CPC 与 HS 页面继续提供原句、旧表及证据入口。 [WCO 第 94 章第 4 页](https://www.wcoomd.org/-/media/wco/public/global/pdf/topics/nomenclature/instruments-and-tools/hs-nomenclature-2022/2022/2094_2022e.pdf?la=en#page=4) · [上一轮范围复核](23-CPC-HS-BOUNDARY-FOLLOWUP.md)

目录中的 18 个证据记录带原件 URL、版本、SHA-256、表格单元格或 PDF 页及文本行定位。CPC 绑定可直接进入具体定义、纳入或排除原句。HS 绑定可进入原目录条目并从证据面板打开对应 PDF。来源页的 Atlas 回链按同一绑定 ID 返回具体商品范围。构建从锁定资料重算，公开目录只保存 Atlas 编写的范围、关系和证据定位。 [锁文件](../data/resources.lock.json) · [构建实现](../atlas_sources/trade_goods.py)

首次复现按前次报告补齐 22 份锁定资源。本轮使用现有资料，构建与 Chrome 验收可离线运行。 [完整采集命令入口](23-CPC-HS-BOUNDARY-FOLLOWUP.md#复现与验收)

```sh
python3 -m atlas_sources validate
python3 -m atlas_sources cpc
python3 -m atlas_sources report
python3 -m unittest discover -s tests -v
node scripts/check_cpc_browser.js
open data/reports/registry.html
```

Chrome 156.0.8078.80 在离线环境中从注册表打开样板，实际展开四层目录，点击灯串到 CPC 排除原句及 HS 子目，并分别回查 Atlas。测试核对了灯具冲突与章鱼候选，验证全部 19 条 Atlas 记录的正反向渲染，以及既有 184 条 CPC 原句到 HS 节点的回查。灯串工作簿及税则 PDF 由 Chrome 打开或下载并校验 SHA-256。临时目录只复制锁定原件和来源登记，页面、公开目录及构建报告 3/3 逐字节一致。100 项单测以及 ISIC、家具目录的 Chrome 回归均通过。 [Chrome 验收脚本](../scripts/check_cpc_browser.js)
