# 家具离线浏览试点

2026-11-09 从来源注册表选择「01-economy · 经济活动」，打开「家具离线目录」。目录可切换 ISIC、NACE 和法国 NAF 的六个原目录分支及 Atlas 家具目录。节点链接用原有稳定 ID 定位，可用浏览器返回键回到上一节点。「返回经济活动来源注册表」恢复经济活动筛选。

## 法国 NAF 案例实测

| 从哪里进入 | Chrome 离线实测 |
|---|---|
| 旧版 `FR_NAF:Rev.2:31.01Z` 的已审反查 | 打开「木制店铺柜台和展柜整品制造中的内置件装配」。Atlas 到旧 `31.01Z` 和新 `31.00G` 的绑定均为 `broadMatch`，可分别返回来源。旧版证据 `FN001` 打开锁定说明 PDF 的 `#page=422`。 |
| 旧版 `31.01Z` 的待审反查 | 打开「木制店铺家具内置部件制造」。旧版绑定仍为 `pending_specialist_scope`，关系字段为 `null`，可从候选区回到 `31.01Z`。浏览器返回键恢复同一 Atlas 节点。 |
| 新版 `FR_NAF:2025:31.00G` 的已审反查 | 整品和独立部件均可回查。独立部件到新版的绑定为 `broadMatch`，展开 `FN003` 核对法文制造条款，打开锁定说明 PDF 的 `#page=160`。 |
| 旧新目录之间的官方对应 | 正向 `NAF rév. 2 vers NAF 2025` 第 383 行，反向 `correspondance inversée NAF` 第 382 行。两行都保留 Insee 的 `Multiple` 与 Atlas 的范围审查 `relatedMatch`。点开两个工作簿并核对下载件的 SHA-256，再沿对应端链接往返。 |

整品和部件沿用各自的稳定身份 `urn:atlas:concept:df67a84e-39ed-547f-b0f1-8d1dfbf6233e` 和 `urn:atlas:concept:a62f38d1-7dd9-52ae-b515-2d39384f83ac`。旧版共同内容支持整品范围，独立部件的旧 NAF 和旧 ISIC 归属仍待审。 [两版说明与对应研究](17-FURNITURE-NAF-BOUNDARIES.md) · [旧 31.01Z](https://www.insee.fr/fr/metadonnees/nafr2/sousClasse/31.01Z) · [新 31.00G](https://www.insee.fr/fr/metadonnees/naf2025/sousClasse/31.00G) · [Insee 对应表发布入口](https://www.insee.fr/fr/information/8617910)

## 复现与覆盖

在仓库根目录运行。初次安装依赖或缺少锁定资料时，按采集指南安装 Poppler、准备 Python 依赖并运行 `python3 -m atlas_sources collect`。备齐资料后，以下命令均可离线运行。 [采集指南](07-REGISTRY-AND-REPRODUCTION.md) · [经济活动依赖](09-ISIC-ECONOMIC-ACTIVITIES.md)

```sh
python3 -m atlas_sources furniture
python3 -m atlas_sources report
python3 -m atlas_sources reproduce-furniture
node scripts/check_furniture_browser.js
node scripts/check_furniture_view.js
node scripts/check_economy_view.js
python3 -m unittest discover -s tests -q
open data/reports/registry.html
```

- 实测使用 macOS、Chrome `156.0.8078.80`、Node.js `22.21.1` 和 Python `3.10.13`。浏览器使用临时配置，以 `file://` 打开页面，模拟离线并阻断 HTTP 和 HTTPS。脚本发送鼠标事件，检查两个 PDF 已加载、两个工作簿下载件与锁文件一致。可用 `ATLAS_CHROME` 指定 Chromium 可执行文件。 [浏览器验收脚本](../scripts/check_furniture_browser.js)
- 试点载入 141 个源分支节点，其中法国旧版 16 个、新版 15 个。自有目录 33 个节点，展示 114 条已审绑定、13 条待审绑定、65 条有独立审查的官方行和 183 条证据。原始文件、版本、审查数据和公开目录与上一提交逐字节一致。干净重建 28/28 份产物一致，95 项 Python 单测及两项 DOM 检查通过。 [家具实测数据](../data/reports/furniture-alignment.json) · [逐文件复现](../data/reports/furniture-reproduction.json)
- 在临时目录分别模拟浏览页未生成、浏览页过期和本地原件缺失。三个状态均隐藏打开入口并显示对应的恢复命令。注册表状态以最近一次 `report` 的检查为准，移动资料后运行 `report` 更新提示。工作簿链接打开完整文件，页面另列工作表与行号。原始资料和带节选的生成页按既有许可边界留在本地。
- 首轮普通沙箱内的 Chrome 启动以 `SIGABRT` 退出。获准使用隔离的临时浏览器配置后，法国案例的导航与证据加载通过验收。

## NACE 和 ISIC 分支扩展实测

2026-11-09，在同一 Chrome 离线验收中，从法国案例继续切换目录、搜索代码、点击原目录与 Atlas 的互查链接。相关节点现直接显示固定表缺行核查，可展开相邻行、原件、起止节点和独立的 Atlas 研究关系。页底审计区保留完整入口。

| 案例 | 双向回查与原件 |
|---|---|
| 新制家具表面处理 | 旧 NACE `31.09` 回查已审的泛材料活动和家用活动家具独立承包涂装。旧 `31.01` 从待审区互查，保留发布者对应与旧定义冲突及空关系。实开旧 NACE Cellar 注释结果第 76 行所在文件、旧 NACE 手册物理第 194 页与当前→旧对应 `Sheet0` 第 555 行所在工作簿。 |
| ISIC 材料分配 | 泛材料活动与 Rev.5 `310` 组双向已审，`3101`、`3102` 可分别待审回查泛材料活动、已审回查木质和全金属子活动。实开 ISIC 更新说明主表第 299–301 行所在工作簿，核对 Rev.4 `3100` 的第 187–188 行各保留拆分标记 `RC4.1`。 |
| 陶瓷家具 | 旧 NACE `23.42`、当前 NACE `31.00` 及两版 ISIC `2393` 均可与 Atlas 活动往返。旧 NACE 历史转换记录继续可见。实开旧→当前第 333 行所在官方对应和当前 NACE 说明第 409 行所在工作簿，并从对应两端往返。 |
| 陶瓷卫生洁具 | 两版 NACE `23.42`、旧 ISIC `2392`、新 ISIC `2393` 均可与独立的 Atlas 活动往返。实开旧 ISIC 数据库压缩包、旧 NACE 手册物理第 153 页、当前 NACE 和 ISIC 说明，以及 2024 年 ISIC 原说明物理第 71、72 页和 2026 年修订工作簿 `Notes` 第 26 行所在文件。 |

| 缺行核查方向 | 固定发布记录 | 实测 |
|---|---:|---|
| UNSD ISIC Rev.4 `2392` → ISIC Rev.5 `2393` | 605 | 展开相邻第 123、124 行，下载原工作簿。 |
| UNSD ISIC Rev.4 `2392` → NACE Rev.2 `23.42` | 996 | 展开相邻第 249、250、253 行，打开原文本，保留 `ISIC4part=1`。 |
| Eurostat Cellar NACE Rev.2 `23.42` → ISIC Rev.4 `2392` | 996 | 打开原 JSON，定位相邻三组结果行 498–500、501–503、513–515，保留发布者 `closeMatch`。 |

三个缺行卡片均沿起止节点往返。官方关系 ID 保持为空，已审的卫生洁具范围继续由单独的 `relatedMatch` 研究关系记录。浏览器打开的原件和实际下载件都核对了锁定哈希。缺行结论限于所列快照，当前 NACE Rev.2.1 与 ISIC Rev.5 的直接官方发布依据仍为开放问题。 [材料与缺行研究](15-FURNITURE-MATERIAL-BOUNDARIES.md) · [独立承包研究](16-FURNITURE-CONTRACT-PARTS-RECHECK.md) · [UNSD 两版对应工作簿](https://unstats.un.org/unsd/classifications/Econ/tables/ISIC/ISIC_Rev4_to_ISIC_Rev5_Correspondence_Table-17Jan2025.xlsx) · [Eurostat 对应入口](https://ec.europa.eu/eurostat/web/nace/correspondence-tables)

Chrome `156.0.8078.80` 实测 `1440×1000` 双列及 `390×844`、`320×760` 单列布局，并人工检查这三个视口的截图。基线在 320 像素宽时扩展到 337 像素；修复后展开缺行完整记录仍可在视口内换行，原件链接完整显示。窄屏点击缺行端点后，焦点和可视区域都落到新节点详情。布局验收限于 Chrome 的三个视口。截图可留在本地生成目录：

```sh
ATLAS_BROWSER_SCREENSHOTS=data/local/furniture-browser-check node scripts/check_furniture_browser.js
```

四个新增验收分支合计 110 个可浏览源节点，其中 NACE Rev.2 与 Rev.2.1 分别为 31、25 个，ISIC Rev.4 与 Rev.5 分别为 29、25 个。原始文件、锁文件、规范化目录和公开审查数据与 `ae08537` 逐字节一致。95 项 Python 单测、两项 DOM 检查、28/28 份干净重建及包含法国案例和资料状态的 Chrome 离线回归均通过。 [NACE/ISIC 验收脚本](../scripts/check_furniture_nace_isic.js) · [家具实测数据](../data/reports/furniture-alignment.json) · [逐文件复现](../data/reports/furniture-reproduction.json)
