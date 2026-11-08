# ISIC 经济活动领域：定义、注释与可追溯对应

本轮将上一轮已验证的 `6563d31` 快进推送到 `main`，随后继续来源资料、本地解析和经济活动整理。同一最终目标下，本轮得到完整的两版源结构、类级官方对应与一小组经证据审查的研究概念，没有创建现实实体连接或需求分类理论。

## 官方输入与资料状态

所有原件继续按 `source + edition + resource + SHA-256` 保存，原字节不变。两版分类、注释更正日期与对应表依据分别记录：

| 资料 | 官方依据/日期 | 用途 |
|---|---|---|
| [Rev.4 官方数据库 ZIP](https://unstats.un.org/unsd/classifications/Econ/Download/In%20Text/ISIC_Rev_4_english_database.zip) | Rev.4；随包 Readme 列出 2009–2011 的五项更正 | 读取原始结构、标签、包含及排除说明 |
| [Rev.4 手册](https://unstats.un.org/unsd/classifications/Econ/Download/In%20Text/ISIC_Rev_4_publication_English.pdf) | 2008 出版；307 个 PDF 页 | 保留纸质版依据，逐页提取说明和方法文本 |
| [Rev.5 结构及注释工作簿](https://unstats.un.org/unsd/classifications/Econ/Download/ISIC5_Exp_Notes_19_Aug_2026.xlsx) | 2026-08-19 更新 | 830 个源节点及包含、补充包含、排除等字段 |
| [Rev.5 白皮版手册](https://unstats.un.org/unsd/classifications/Econ/Download/ISIC_Rev5_Publication-white_cover_version.pdf) | 2026；出版号仍待分配；335 个 PDF 页 | 保留导言、应用规则与解释说明 |
| [Rev.5 勘误](https://unstats.un.org/unsd/classifications/Econ/Download/Errata_for_the_Explanatory_Notes_of_the_ISICRev5_-_2026.pdf) | PDF 标 2026-08-17；66 页 | 勘误依据；以工作簿保存的原说明/新说明逐项比较 |
| [Rev.4→5 对应工作簿](https://unstats.un.org/unsd/classifications/Econ/tables/ISIC/ISIC_Rev4_to_ISIC_Rev5_Correspondence_Table-17Jan2025.xlsx) | 内部 Note 页明确 2025-01-17 更新 | 全部类级对应、GSIM 类型、变化说明及原始单元格 |
| [对应技术说明 PDF](https://unstats.un.org/unsd/classifications/Meetings/UNCEISC2024_2nd/Session_6_Bk_2_Technical_Note.pdf) | 2024-10-25；1 页 | 历史编制说明；不覆盖工作簿中较晚的 Note 页 |

另保留上一轮两版结构 CSV。本轮新增六个资源并全部真实下载，两轮复取的六个 SHA-256 一致。全项目目前为 18 个资源任务、16 个实得文件、2 个许可状态阻止；仍涉及 6 个分类来源。

UNSD 对外完整再分发条件尚未确认，因此这些原件、完整注释、完整 605 行对应及完整源衍生目录仍在被 Git 忽略的 `data/local/`。公开提交只增加资源元数据、哈希、实测统计、14 个选定案例的代码/GSIM事实、我们自己的审查说明，以及3个研究概念的稳定ID和来源关联；不复制官方完整定义、变化说明或整张对应表。

## 实测定义和层级覆盖

| 项目 | Rev.4 | Rev.5 |
|---|---:|---:|
| 全部源节点 | 766 | 830 |
| 四层节点分布 | 21 / 88 / 238 / 419 | 22 / 87 / 258 / 463 |
| 非空独立说明 | 764 | 830 |
| 类级节点有说明 | 419 / 419 | 463 / 463 |
| 与原结构的代码、父级、标签差异 | 0 | 0 |
| 重复码、孤儿、自引用、循环 | 0 | 0 |

Rev.4 的 `089`、`T` 在数据库中没有独立说明；已对照手册 PDF 的第99页（印刷页83）和第285页（印刷页269）进行渲染核查，纸质版也未在这些标题后提供独立说明。保留为空，不用子类说明或模型文字补写。

Rev.4 的五项数据库更正均做了具体文本检查：3830、1313、1811、51、3315。原始 Readme 全文和数据库表保留在本地，不把更正版内容伪称为原始2008纸质版。Rev.5 保留工作簿 Notes 页的50条修订，包括原2024说明、新2026说明、更改理由和性质。相应代码仍属于 Rev.5，但明确带有注释组件日期，不与2025对应依据混写。

## 对应解析及语义

605 行全部保留，605 个不同的代码对，覆盖 Rev.4 的419个类与 Rev.5 的463个类。每条对应保存原始四位代码、带节字母代码、原始行/列、GSIM 原文与解析类型、变化说明、证据文件哈希、版次依据、双向对应数量和范围判定。

| 对应图中的行类型 | 行数 |
|---|---:|
| 一对一 | 286 |
| 一对多 | 123 |
| 多对一 | 17 |
| 多对多 | 179 |

以上按边/行统计，不是将同一个拆分案例重复计作多个不同旧类。GSIM 支持复合类型：代码变化、名称变化、分解、分出、合并、接收和转移均保留，不能只选择其中一个类型。原文中 `Split off` / `Split-off`、拼写差异及问号均保留；解析只提取其类型标识。

每条边另外给出 `from_scope / to_scope = whole / partial` 及方向明确的 SKOS 研究候选。这些范围是依据完整对应图推导的研究字段，**不是发布者直接给出的占比**：

- 旧类拆向多个新类时，每条边只涉及旧类的一部分。
- 多个旧类进入同一新类时，每条边只涉及新类的一部分。
- 双方均有多个对应时保留部分重叠，不能视为等价。
- 一对一仍需检查 GSIM；存在真实范围变化时不自动得到 `exactMatch`。
- 所有分配权重均为空；本工具不能据此自动换算统计数值。

方向始终为 Rev.4 → Rev.5：`narrowMatch` 表示新端比旧端窄，`broadMatch` 表示新端比旧端宽。候选关系不等于已审概念关联。

特别保留三种需要检查的情况：

1. **空白 GSIM 不足以确证等价**。5 行的 GSIM 为空但完整对应图中存在多重关系（物理行4、25、115、136、466）。例如旧 `0113`→新 `0113` 的行没有类型文字，但新 `0113` 还接收旧 `0128` 的转移活动，因此不能只看本行同码而合并。
2. **旧带节代码异常**。第19、33行分别记录 `A013A0`、`A017A0`，四位端点为 `0130`、`0170`；其变化说明也提到字母数字代码错误更正。解析以明确的四位端点连接源目录，同时原样保留旧带节字符串、预期结构代码及待审状态，不改写原件。
3. **发布者问号**。第530行 `8522`→`8532` 的 GSIM 带 `?`，单独标记发布者不确定；关联的另一去向 `8533` 也保留，不能删除不便处理的边。

## 历史对应与2026注释的边界

工作簿对应是以2024采用的注释为基础、在2025更新的官方陈述；2026注释的更新不能倒写为该表已经重新审定。工具分别保留 `historical_skos_candidate` 与 `current_skos_candidate`。

50条更新中的上级代码也会影响其下级类的审查。例如某个 division 的范围说明更新，不应只对该 division 设标记而忽略 class。受更新影响的当前对应保持待审；历史GSIM原文不变。

当前605行的主要审查状态为：248条有官方范围等价证据的候选、182条真实变化待审、169条后续注释待审、3条无GSIM但图关系复杂待审、2条带节标识待审、1条发布者问号。该状态按优先项互斥统计；原始复合类型和全部问题字段仍独立保存。

## 已审的小组研究概念

`data/research/isic-review-decisions.json` 保存14个明确案例及我们自己的理由，绑定三份关键输入的已审 SHA-256。源字节变化或关系条件变化会使旧决定失效，必须重新研究，不能静默继承。

其中3个简单案例（`0111`→`0111`、`4661`→`4671`、`1512`→`1512`）依据官方无变化/虚拟变化语义、双向唯一对应、完整来源说明和无相关勘误影响，建立3个稳定的 Atlas 研究概念，产生6条来源绑定。11个复杂或不确定案例继续保留。审查者明确记为 Codex，不冒称用户/机构审批。

公开索引 `data/atlas/economy/reviewed-concept-index.json` 可从 Atlas ID 查回两版源节点，也可从源节点反查 Atlas ID。完整源名称/说明仍从本地快照解析，尚未形成全领域的自有统一目录；这3个概念是一组已审研究结果。其余248个候选不会在运行时批量变成已审概念。没有自动概念合并。

## 复现

基础工具继续使用 Python 标准库。ISIC4 Access 读取另需固定版本依赖，PDF文本需 Poppler 的 `pdftotext`：

```sh
python3 -m pip install -r requirements-isic.txt --target data/local/deps
# macOS 如缺少 pdftotext：brew install poppler
python3 -m atlas_sources validate
python3 -m atlas_sources collect
python3 -m atlas_sources verify
python3 -m atlas_sources economy
python3 -m atlas_sources report
python3 -m unittest discover -s tests -v
open data/local/economy/isic/index.html
```

`collect` 按锁文件重取缺失资料；`--refresh` 实测上游变化，保留旧快照。UNSPSC、SNOMED 仍因权利状态阻止，不发出其下载请求。`economy` 在输入、校验或依赖失败时返回1并报告具体原因；没有将缺失说明伪装为成功采集。

主要输出：

```text
data/local/economy/isic/rev4-nodes.jsonl
data/local/economy/isic/rev5-nodes-20260819.jsonl
data/local/economy/isic/correspondence-20250117.jsonl
data/local/economy/isic/rev5-note-revisions.json
data/local/economy/isic/*-pages.jsonl
data/local/economy/isic/reviewed-atlas-concepts.json
data/local/economy/isic/source-to-atlas.json
data/local/economy/isic/index.html
data/reports/isic-economy.json
data/reports/isic-reviewed-cases.json
data/atlas/economy/reviewed-concept-index.json
```

本地浏览器支持两版源树、代码/名称/说明搜索、包含/排除文本、父级、官方对应、GSIM、原表位置、哈希、历史/当前状态、2024/2026说明比较和已审概念的双向追溯。生成文件不联网加载资料。脚本语法检查通过；受当前工具的本地文件浏览策略限制，本轮没有声称完成浏览器视觉验收。

## 验证、失败及下一步

30 项回归通过，覆盖前导零、稀疏单元格、XML文本转义、复合GSIM、部分对应方向、空白GSIM接收转移、问号、父级勘误传播、来源标识异常保真、重复边拒绝、已审字节约束和采集完整性。还在不含任何既有派生结果的干净目录内，仅使用锁定原件和同版本依赖重建了17个输出，全部逐字节一致。报告记录实际 Python、Access 依赖、Poppler版本及解析代码哈希；不同 Poppler 版本可能改变PDF文本布局，应对照其提取器记录。

最初的严格带节代码校验在 `A013A0` 处失败，随后改为保留异常原值并使用独立四位代码和源结构校验端点。失败保存在 `data/reports/isic-extraction-failures.jsonl`，没有删除该行或改写原件来通过检查。

后续仍需：继续审查拆分/合并/转移与2026范围澄清；核实UNSD公开再分发条件；在同对象下扩展NAICS/NACE等官方对应；随后才将更多已解释的源概念加入自有目录。范围不同、证据不足和待映射条目继续并存，不以覆盖率替代语义依据。
