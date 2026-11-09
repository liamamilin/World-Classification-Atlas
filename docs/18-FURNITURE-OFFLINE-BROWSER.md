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
- 普通沙箱内的 Chrome 启动以 `SIGABRT` 退出。获准在隔离的临时浏览器配置下运行后，上述 Chrome 验收通过。验收覆盖该案例的导航与证据加载，其他来源分支的实际浏览路径及视觉布局仍待专项验证。
