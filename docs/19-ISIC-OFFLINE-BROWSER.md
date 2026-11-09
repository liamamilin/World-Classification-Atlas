# ISIC 经济活动离线浏览实测

2026-11-09 使用 Chrome `156.0.8078.80` 从来源注册表的「经济活动」进入 ISIC 离线目录。目录可切换 Rev.4、Rev.5 与 Atlas 局部目录，按代码和说明搜索。原目录、Atlas 活动和待审提案都可用原有稳定 ID 定位，来源链接支持浏览器返回。登记页在资料缺失、浏览页未生成或浏览页过期时显示各自的恢复命令。返回注册表恢复经济活动筛选。 [浏览器验收脚本](../scripts/check_economy_browser.js)

| 案例 | 实测路径与原件 |
| --- | --- |
| 无调味直接食用水冰 | 从待审提案分别往返 Rev.5 `1050` 和 `3530`，核对 `Notes` 第 14、35 行的 2024 原说明和 2026 更新。实开 CPC 2.1 工作簿第 512、765 行所在文件和手册物理第 56 页。旧 `3530` → 新 `1050` 在研究补充区双向可查，保留 `held_after_research` 和空关系。官方 `3530` → `3530` 第 209 行在官方区双向可查，原新范围均显示 `whole`，Atlas 审查为 `relatedMatch`。水冰提案没有已批准的来源绑定。 |
| 防护口罩 | 从 Rev.5 `3250` 分别往返外科、FFP2、FFP3 三个当前版已审活动，实开主表第 313 行所在工作簿。三个活动与旧 `1392`、`3250` 的六条来源候选均可从待审区双向回查。旧 `1399` → 新 `3250` 的研究补充继续暂缓。实开 `Notes` 第 20 行和 CPC 2.1 第 2529 行所在工作簿，核对当前排除条款与产品旁证。 |
| 碳纤维织物 | 从旧 `1312` 和新 `2399` 双向回查已审织造活动，实开旧数据库、当前主表第 127 行所在文件和 CPC 手册物理第 87 页。旧 `2399` 仍可从待审区往返竞争织造来源，独立的碳纤维本体制造仍在已审区。研究补充的 `relatedMatch` 与官方表分开。实开 `Notes` 第 17 行所在工作簿，保留玻璃原料例项修订和碳制品排除的各自位置。 |
| 官方部分对应对照 | 食品分支旧 `1079` → 新 `1076` 的第 72 行保留 `RC4.2` 和 `one_to_many`。从两端查看同一行均显示原范围 `partial`、新范围 `whole`，范围来自完整对应图。实际下载官方工作簿并核对哈希。 |

实测打开的原件或浏览器下载件均按锁文件核对 SHA-256。勘误来自官方更新工作簿的 `Notes` 页。原版数据库、工作簿和手册节选均使用已有资料和证据区间。此次试点覆盖三组边界案例和一条官方部分对应对照。无调味水冰、旧版口罩归属和旧 `2399` 的织造范围仍按既有审查记录待核。 [三项研究依据](12-ISIC-BOUNDARY-FOLLOWUPS.md) · [UNSD Rev.5 更新说明工作簿](https://unstats.un.org/unsd/classifications/Econ/Download/ISIC5_Exp_Notes_19_Aug_2026.xlsx) · [UNSD 官方两版对应表](https://unstats.un.org/unsd/classifications/Econ/tables/ISIC/ISIC_Rev4_to_ISIC_Rev5_Correspondence_Table-17Jan2025.xlsx) · [CPC 2.1 更正说明工作簿](https://unstats.un.org/unsd/classifications/Econ/Download/In%20Text/CPC_Ver_2.1_Exp_Notes_Updated_3Apr2025.xlsx)

目录可浏览 Rev.4 的 766 个和 Rev.5 的 830 个源节点、263 个 Atlas 节点、605 条官方对应及 50 条勘误。130 条定位证据、7 条待审来源关联和 1 项独立待审提案沿用原审查结果。公开目录、原始快照、锁文件和审查输入与 `981ff5e` 逐字节一致。生成页和含节选的资料按既有许可边界保存在本地。 [ISIC 实测数据](../data/reports/isic-economy.json) · [逐文件重建](../data/reports/isic-reproduction.json)

首次 Chrome 走查在旧制冰条款的测试断言处失败。改为按旧数据库实际使用的食用与非食用表述校验后，离线走查通过。临时目录的缺页、过期页和缺资料三种提示通过。95 项 Python 单测、两项 DOM 检查及家具 Chrome 回归通过。干净目录重建 ISIC 35/35、家具 28/28 份产物逐字节一致。

## 植物奶、食品冰与核燃料扩展

2026-11-09 使用同一 Chrome 离线环境扩展验收。相关勘误展开后可从「手册与勘误 PDF 旁证」打开已锁定的 PDF 物理页。试验从注册表进入，分别核对六个既有 Atlas 活动的来源往返、两条已审研究补充的双向路径，以及七条官方对应的原发布方向和范围。原版数据库、更新工作簿、官方对应工作簿、手册和勘误 PDF 都通过锁定哈希校验。 [原有逐条审查](11-ISIC-PRIORITY-ALLOCATIONS.md) · [2026 勘误 PDF](https://unstats.un.org/unsd/classifications/Econ/Download/Errata_for_the_Explanatory_Notes_of_the_ISICRev5_-_2026.pdf) · [Rev.5 白皮版手册](https://unstats.un.org/unsd/classifications/Econ/Download/ISIC_Rev5_Publication-white_cover_version.pdf)

| 案例 | 实测路径和证据 |
| --- | --- |
| 植物奶 | 从旧 `1079` 和新 `1105` 往返植物奶活动。旧数据库明确列非乳奶，新主表第 120 行列植物饮料，第 100 行把植物奶排到 `1105`。`Notes` 第 15 行显示新 `1079` 保留奶酪替代品，第 16 行保留 `1105` 的原文差异。实开白皮版物理第 109 页，和主表的植物饮料例项对读。`TEXT-2026-1105` 为研究澄清，发布者解决状态仍为 `not_obtained`。`1079 → 1105` 为范围限定的 Atlas 研究补充，官方缺行保留。 |
| 食品冰 | 冰淇淋及雪葩从两版 `1050` 往返，冷却用途水冰从两版 `3530` 往返。`Notes` 第 14 行记录食品冰列项归并和植物奶排除目的的更新。第 35 行显示 `3530` 在 2024 与 2026 说明中均将食品冰指向 `1050`，2026 增列冷却用途限定。实开白皮版物理第 103、178 页。无调味直接食用水冰仍从待审提案入口回查。 |
| 核燃料 | 铀钍矿富集 `2011 → 2011`、燃料元件制造 `2011 → 2420` 和天然铀冶炼精炼 `2420 → 2420` 分别沿两版来源往返。打开旧数据库、新主表第 174、208 行所在工作簿，以及 `Notes` 第 22、27 行。实开勘误 PDF 物理第 16、24 页和白皮版第 135 页。`2011 → 2420` 仅为燃料元件活动的研究补充，官方缺行保留。 |

| 官方表行 | 两端核对的范围与已审活动 |
| --- | --- |
| 72、73 | 旧 `1079` 分到新 `1076`、`1079`，均为 `RC4.2` 和 `partial → whole`，分别回查咖啡与奶酪替代品。 |
| 64 | `1050 → 1050` 显示 `whole → whole`，GSIM 为空，Atlas 保留范围限定的 `relatedMatch`，可回查冰淇淋及雪葩。 |
| 108、109、115、130 | `2011 → 2011` 为 `partial → whole`，回查铀钍矿富集。 `2011 → 2029` 为 `partial → partial`，回查发酵生物乙醇燃料。 `2029 → 2029` 为 `whole → partial`，回查胶黏剂。 `2420 → 2420` 为 `whole → whole`，回查天然铀冶炼精炼。第 108、109 行保留 `RC5`。 |

95 项 Python 单测和离线 DOM 检查通过。ISIC Chrome 全量验收含首轮案例和三种资料状态提示，干净重建的 35 份产物逐字节一致。原始文件、稳定 ID、冲突、待审记录和公开审查输入与 `03ee1ab` 一致。浏览器验收覆盖所列样本，语义结论限于既有审查和固定快照。 [浏览器验收脚本](../scripts/check_economy_browser.js) · [逐文件重建](../data/reports/isic-reproduction.json)

已有锁定资料和依赖时，在仓库根目录离线执行下列命令。缺少资料时先按锁收集，具体依赖见采集与 ISIC 复现说明。 [采集说明](07-REGISTRY-AND-REPRODUCTION.md) · [ISIC 依赖](09-ISIC-ECONOMIC-ACTIVITIES.md)

```sh
python3 -m atlas_sources reproduce-economy
python3 -m atlas_sources report
node scripts/check_economy_browser.js
open data/reports/registry.html
```
