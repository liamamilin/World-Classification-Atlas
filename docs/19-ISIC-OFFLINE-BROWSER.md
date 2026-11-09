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

已有锁定资料和依赖时，在仓库根目录离线执行下列命令。缺少资料时先按锁收集，具体依赖见采集与 ISIC 复现说明。 [采集说明](07-REGISTRY-AND-REPRODUCTION.md) · [ISIC 依赖](09-ISIC-ECONOMIC-ACTIVITIES.md)

```sh
python3 -m atlas_sources reproduce-economy
python3 -m atlas_sources report
node scripts/check_economy_browser.js
open data/reports/registry.html
```
