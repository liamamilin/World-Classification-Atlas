# 法国 NAF 双向对应与家具活动边界

2026-11-09 · 法国 NAF rév. 2 / NAF 2025、NACE Rev.2 / Rev.2.1、ISIC Rev.4 / Rev.5

## 新增来源与实测结构

本轮从 Insee 获取六个文件。NAF rév. 2 的代码路径来自五级嵌套 DBF，NAF 2025 的结构来自2026年10月更新工作簿。旧2020年再版说明和新2025年版说明分别存档，双向对应采用2026年10月版。Insee 将2027年1月列为 NAF 2025 用于 APE 编码的时间。结构 DBF 与三个工作簿依 Licence Ouverte 2.0 入库。两个说明 PDF 原件及选段保留在本地。 [旧版入口](https://www.insee.fr/fr/information/2120875) · [2025版入口](https://www.insee.fr/fr/information/8617910) · [实施说明](https://www.insee.fr/fr/information/8181066) · [再利用条款](https://www.insee.fr/fr/information/2008466?page=copyright.htm)

| 版次 | 节 | 部 | 组 | 类 | 法国子类 | 节点合计 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| NAF rév. 2 | 21 | 88 | 272 | 615 | 732 | 1,728 |
| NAF 2025 | 22 | 87 | 287 | 651 | 747 | 1,794 |

旧 DBF 本身提供代码与父级。旧子类的732个标题来自 Insee 旧→新对应工作簿，节点分别记录结构及标题来源。旧上层未由此补写标题。新结构的组合页和各层级页代码集一致。2025年说明第2物理页称有21节，2026年10月结构工作簿实测 A 至 V 共22节。两份原始记录和计数差异分别保留。两版说明本轮只提取8段相关子类说明，旧31.01Z的标题在物理第420页，说明续在第422页，间隔的第421页为产品 CPF。 [2025年版说明](https://www.insee.fr/fr/statistiques/fichier/8617910/NAF2025%20-%20Notes%20-%20Edition%202025.pdf) · [结构及实测](../data/reports/furniture-alignment.json)

两个对应工作簿各有1,242行，其中各有1行记录同一个无旧端点的新子类 `46.89Y`。完整代码对反转后相同。共同内容字段有954对原文不同，其中包括各方向的通用范围描述。发布者的 `Unique`、`Multiple` 依各方向原样保存。专门的活动审查仍按共同内容、两端说明和活动对象逐项决定。 [Insee 发布入口](https://www.insee.fr/fr/information/8617910) · [真实采集记录](../data/acquisition/20261109T011424093656Z-b9c0b825.json)

## 专业家具的独立涂装

旧 NAF `31.09B` 到新 `31.00G` 的两张表第391和385行，明确列出专业用途其他家具的表面处理。旧 `31.01Z` 与新 `31.00G` 的第383和382行列办公和店铺整品制造，未单列独立涂装。旧法国说明另列本类座椅制造阶段的软包。法国的逐条内容与欧洲表第555行将泛称工序列入旧 NACE `31.01` 的证据并列。 [旧法国31.09B](https://www.insee.fr/fr/metadonnees/nafr2/sousClasse/31.09B) · [旧法国31.01Z](https://www.insee.fr/fr/metadonnees/nafr2/sousClasse/31.01Z) · [Eurostat 对应](https://ec.europa.eu/eurostat/web/nace/correspondence-tables)

按承包者处理已可识别新家具的范围，审定专业用途其他家具涂装，旧端采用 NACE `31.09` 和 NAF `31.09B`。专用办公及店铺柜台、展柜的独立涂装另建活动，审定两代 ISIC、当前 NACE 与法国 `31.00G` 的共同范围。旧 NACE `31.01`、`31.09` 和旧法国 `31.01Z` 在该专用活动下保留候选。两项新活动的 Rev.5 家具绑定都为组级。既有家用其他家具涂装补入法国 `31.09B` 和 `31.00J` 的来源绑定。 [法国31.00G](https://www.insee.fr/fr/metadonnees/naf2025/sousClasse/31.00G) · [法国31.00J](https://www.insee.fr/fr/metadonnees/naf2025/sousClasse/31.00J)

## 店铺整品、部件与安装

木制店铺柜台和展柜制造中装配内置件，产出是整品。两代 ISIC 均列店铺家具制造，旧版可对该整品范围绑定 `3100`。独立产出木制专用内置件是既有另一活动，新增法国 `31.00G` 的明确制造条款。法国旧 `31.01Z` 关联的泛家具部件 CPF `31.00.20p` 属于部分产品旁证。两个法国整品共同内容字段均未单列内置件制造，独立部件的法国旧版和旧 ISIC 候选继续保留。 [ISIC Rev.4 3100](https://unstats.un.org/unsd/classifications/Econ/Detail/EN/27/3100) · [法国31.00G](https://www.insee.fr/fr/metadonnees/naf2025/sousClasse/31.00G)

木制店铺固定装置的现场安装新增独立活动，连接 ISIC `4330`、NACE `43.32`、旧法国 `43.32C` 和新法国 `43.32G`。法国两表第493和492行的共同内容含木材和PVC作业，Atlas 审查限木制现场安装。现场安装与整品和部件制造分别索引。 [旧法国43.32C](https://www.insee.fr/fr/metadonnees/nafr2/sousClasse/43.32C) · [法国43.32G](https://www.insee.fr/fr/metadonnees/naf2025/sousClasse/43.32G)

## 卫生洁具对照

法国旧 `23.42Z` 到新 `23.42Y` 的第239行列卫生洁具，第240行将陶瓷厨卫家具分向 `31.00H`。反向第241行使用整个新卫生洁具子类的表述，保留 `Unique` 与旧→新的 `Multiple` 区别。既有卫生洁具活动补入法国两版说明绑定及两方向记录。前轮的三处 ISIC 相关官方缺行记录独立保存，法国国家表提供可比较的明文分流。 [Insee 对应入口](https://www.insee.fr/fr/information/8617910) · [公开活动目录](../data/atlas/economy/furniture-directory.json)

## 验证与复现

- 注册表有53个来源、53项采集任务和51份固定快照，覆盖10个有本地文件的来源。本轮六个 Insee 文件均下载成功。网页浏览工具无法读取部分表格格式，实际文件由采集器下载并通过哈希和专项解析验证。UNSPSC 与 SNOMED CT 仍标为 `blocked_rights`。
- 家具目录33个节点，含25项活动、6个导航和2个复用锚点，保留上一轮29个稳定 ID。新增4项活动、42条证据、11条已审官方行和5条 Atlas 研究关系。总计65条已审官方行、28条研究关系、183条证据、114条已审绑定和13条待审绑定。
- 38份固定源输入用于家具复现。家具28/28、ISIC 35/35份产物逐字节一致。首次单测的两项旧断言依赖来源集合或候选位置，改为按指定来源和稳定代码核对后，95项单元测试和两项离线 DOM 检查通过。页面检查覆盖数据和交互，视觉布局未验收。

从仓库根目录运行。已有快照时家具重建无需网络。Poppler 和 Access 依赖的说明见 [ISIC 复现指南](09-ISIC-ECONOMIC-ACTIVITIES.md)。

```sh
python3 -m pip install -r requirements-isic.txt --target data/local/deps
python3 -m atlas_sources validate
python3 -m atlas_sources collect
python3 -m atlas_sources verify
python3 -m atlas_sources reproduce-furniture
python3 -m atlas_sources reproduce-economy
python3 -m atlas_sources report
python3 -m unittest discover -s tests -q
node scripts/check_furniture_view.js
node scripts/check_economy_view.js
open data/local/economy/furniture/index.html
```

两版法国完整代码结构、两个方向的规范化对应和选定说明均输出至 `data/local/economy/furniture/naf-*.jsonl`。离线浏览可切换两版法国分支，并查看共同内容观察和绑定证据。 [审查输入](../data/research/furniture-naf-review.json) · [家具复现报告](../data/reports/furniture-reproduction.json)
