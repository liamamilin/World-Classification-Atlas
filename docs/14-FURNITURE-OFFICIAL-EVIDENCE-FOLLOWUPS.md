# 家具表面处理、旧陶瓷家具与直接官方对应跟进

本轮在`ecc2611`的家具同对象研究上继续：补采官方原方向的旧→新表、独立RDF说明组件和Eurostat直接对应；以具体活动证据处理待审，不以词语、同码或版本链传递合并。原有263节点ISIC目录及其稳定ID独立保留；此前家具目录11个身份全部保留，本轮新增7个身份。没有现实实体关联或需求理论。

## 关键结果

- **新制家具表面处理**：旧ISIC3100、旧NACE31.09、当前NACE31.00和ISIC5的**310组**均直接列出处理活动。新增表面喷涂/涂漆/抛光与首次软包两个有界活动，保留组级绑定。没有将整个泛材料活动强派到3101或3102。
- **旧陶瓷家具**：新增官方旧NACE23.42→新31.00表333行明确列陶瓷家具分配，与原反方向表和旧31.09排除指向一致。旧NACE绑定改为已审的具体活动分配；原候选、理由、证据与转换决定保留。未冒称旧23.42说明直接包含家具，卫生洁具整类冲突仍在。
- **直接官方对应**：采到Eurostat NACE2→ISIC4的996个XKOS关联及独立SKOS谓词，**全部为发布者closeMatch**，不重写成exactMatch。当前NACE2.1–ISIC5在明确定义的审计快照内未观察到直接关系，问题保持开放。
- **完整桥接比较的真实冲突**：995对代码事实与UNSD一致；Eurostat的NACE2 46.6→ISIC4 466，与UNSD的46.6→465不同。既有2011更改历史明确记录466→465更正。两份原值独立保留，不回写RDF；该组不属于家具分支。
- **目录扩展**：增加新家具工序、当前木制专用部件，以及与制造并列的重新软包/表面翻修和固定厨房家具现场安装。部件只审定当前两源，旧版保持待审。

## 官方资料、版次与许可

[Eurostat官方分类入口](https://ec.europa.eu/eurostat/web/metadata/classifications)明确列出ShowVoc、Cellar SPARQL及RAMON档案入口。[建模说明](https://cros.ec.europa.eu/book-page/modeling-eurostats-statistical-classifications-showvoc)和[查询指南](https://cros.ec.europa.eu/book-page/sparql-queries-user-guide)说明如何提取SKOS/XKOS对应。下载清单与[原有对应入口](https://ec.europa.eu/eurostat/web/nace/correspondence-tables)继续作为独立来源，不将网页入口当作已取得全部对应。

NACE版次仍是Rev.2/Rev.2.1。新RDF资料是2026-11-09观察的**分发组件**，不是新的分类revision；2008手册节点不被新说明覆盖。节点保留`canonical_node_id`、原URI、语言/字面量类型、说明字段、官方broader父级与精确结果行。真实URI使用无点数字（如`.../2342`），显示notation仍为23.42，不能直接拼接点号代码后把空结果当不存在。

[Eurostat复用条款](https://ec.europa.eu/eurostat/help/copyright-notice)及已有手册的具体许可核验沿用；本轮公开Eurostat分类元数据、对应和格式转换，署名及修改责任见[ATTRIBUTION](../data/ATTRIBUTION.md)。完整PDF仍因第三方封面例外本地保存；UNSD全文仍本地限制。公共ShowVoc项目清单包含其他发布者，完整清单再分发未审，因此仅本地保存，其哈希和有限核查事实公开。未把EU条款移给UN资料或其他发布者。

本轮10份新增原件全部下载成功。全项目50来源、15导航领域、40任务、38个锁定文件、7个有本地资料的来源；UNSPSC/SNOMED两项权限阻止不变。UTC采集时间在manifest及`data/acquisition/`，本报告日期为Asia/Shanghai的2026-11-09。

| 新增原件 | 字节 | SHA-256 |
|---|---:|---|
| nace2-download-list-20261109 | 3,019 | `5f56913345eb7ee538b525f98023ee575993c2012ecd458bc90f25c15e158a85` |
| nace2-nace21-correspondence-20260831 | 143,261 | `a6f961f00fcc62aff9d44d825e51b483f6ff0d828066dc2bddf31b4040c86dbd` |
| nace-showvoc-catalog-20261109 | 1,155,655 | `0eb2273a5cdec5ff5a61791a3bb403f590e0173992a345d41c2bc8befbc1e51d` |
| nace2-cellar-selected-notes-20261109 | 47,837 | `06997658752f8480ab26a0313fa65fc33d4586e4815efbd2fd62b26db1552ebf` |
| nace2-cellar-isic4-predicates-20261109 | 253,079 | `9181d36e48e4671c982c4732fa6d51d43b997289c76d160dd35d578b62fd5758` |
| nace-cellar-correspondence-schemes-20261109 | 19,469 | `c2eda8bfcfb607c9d8f347277cc1ba922f60a5695dee7bb81205515246948ff8` |
| nace-cellar-current-mapping-targets-20261109 | 307 | `0b99073b0d4331d885e63e7c4b03d96c4115171e91a6c4243f4ac1f62624df5f` |
| nace-cellar-current-positive-control-20261109 | 227 | `2971c1731598bbbbb5cfdc40c7d801a3fd86a01b396c8c46ff1d5060bf3793b8` |
| nace-cellar-nace2-isic4-xkos-20261109 | 835,974 | `ebb2b8f7373f7fe50e4c3b995130c5b29ef2f759ddc375c9f214ee56857907a2` |
| nace-cellar-current-incoming-isic-20261109 | 127 | `6acf2493944f74fe96bb2cabbf77364437dd70911b91261b39c773baa31048d5` |

这些原件不是探测过程生成的模型内容。`data/queries/`的七份只读查询与资源URL中的query参数逐字节相符并锁定哈希；结果按已提交ORDER BY排序，COUNT对照不截断。查询不使用LIMIT/OFFSET或外部SERVICE联邦；本地重建不联网。

## 完整解析与直接对应审计

新增旧NACE2→Rev.2.1表1598行，与已有反方向表的代码对逆向集合一致，但两份原文件与原文字段各自保留。表首46.89的旧端点及Level为空，G列却为1；解析保留`from=null`、`level=null`、`target_level=4`及原G1，计数校验对无源端点明确不适用，不擅改成0、4或虚构源代码。31.01→31.00的Common_Content原为空，也不补写。

Cellar旧NACE选取说明为22节点，与原手册选取14节点并存。XKOS结果2990条原始三元组组成996个关联，另996条显式SKOS closeMatch谓词独立采集；来源、目标、关联URI、谓词、字面量和结果行均保真，未依靠名称补边。与UNSD的对照按代码事实比较，995对一致不意味着995项语义等价。

当前直接对应审计执行四个互补查询：

1. 各命名图中比较NACE2/2.1的XKOS表目录：58行、25个不同表；只统计声明的compares，不猜测表名。
2. 当前NACE2.1所有显式映射的出向目标命名空间：仅观察到旧NACE2。
3. 指向当前NACE2.1全部节点的ISIC入向映射：0行。
4. 当前scheme完整阳性对照：1047节点，与锁定XLSX节点数一致。

公开项目目录另观察256个PUBLIC条目，没有ISIC命名的数据集；这不是证明ISIC不存在。审计状态为`not_observed_in_audited_cellar_snapshot`，有具体图、查询与快照边界；**不等同于发布者声明无对应，也不保证其他入口永远没有直接表**。旧版直接桥已经取得，当前版仍不经多张表传递成为“官方”对应。

## 待审问题逐项处置

| 原问题 | 本轮处理 | 保留的剩余问题 |
|---|---|---|
| FURN-DIRECT-CROSSWALK | 取得旧版官方直接XKOS桥，完成当前版四项命名图审计；状态open | 当前NACE2.1–ISIC5直接发布依据尚未观察到 |
| FURN-FINISHING | 两个新工序活动获四版支持，ISIC5保留310组级；状态partially_addressed | 新材料细类分配未审；当前表把处理列在旧31.01，而2008手册与旧RDF明确31.09，竞争候选关系为空 |
| FURN-CERAMIC-OLD | 依据明确官方活动分配批准旧23.42绑定，并保留候选转换历史；状态partially_addressed | 旧23.42未直接列家具、旧ISIC2392包含卫生洁具而2393排除，与整类跨表陈述的差异继续保存 |
| FURN-NACE-ISIC-GENERALITY | 保留真实直接桥的closeMatch及具体材料边界；状态partially_addressed | 通用“前两级相同”叙述不代替家具具体类范围，当前版直接对应仍缺 |
| FURN-PARTS-RESIDUAL | 新增当前两源的可识别木制家具部件；维修及固定安装与制造并列；状态partially_addressed | 两套旧版部件分配、独立板材和完整加工剩余范围未全审 |

新增`NACE2-ISIC4-46.6-DISAGREEMENT`为`conflict_retained`，保留两个发布者、UNSD更改历史及差异原值。五个旧问题保留原始finding、status和历史，新增followup字段描述本轮处理；没有取得发布者新答复或发送对外信息。现有6项问题为1 open、4 partially_addressed、1 conflict_retained，不能将有界活动批准称作整类问题关闭。

旧陶瓷绑定采用`basis=explicit_official_crosswalk_activity_allocation`，限定具体活动而非整类；程序校验被分配端点、活动key、官方表资源身份和原文区间。它不走多表等价传递，也不伪装成旧定义的直接包含。历史候选可从`source_to_binding_history`反查；活跃候选与批准绑定仍分开。

## 新增活动与目录覆盖

| 新活动 | ISIC4 | ISIC5 | NACE2 | NACE2.1 |
|---|---|---|---|---|
| 新制非矿物家具喷涂、涂漆与抛光 | 3100 | **310组** | 31.09 | 31.00 |
| 新制椅及座椅首次软包 | 3100 | **310组** | 31.09 | 31.00 |
| 可识别木制家具部件（当前范围） | 待审3100 | **310组** | 待审31.0 | 31.00 |
| 使用后家具重新软包与表面翻修 | 9524 | 9524 | 95.24 | 95.24 |
| 固定式厨房家具现场安装 | 4330 | 4330 | 43.32 | 43.32 |

原有七个活动及ID保留，其中陶瓷家具的旧NACE部分获有界分配。活动→来源的broadMatch表示来源比该活动宽；组级证据不冒充类级。维修/安装属于相同的经济活动分类对象，但与制造并列为第二个Atlas导航根，不挂进制造业来源上级。新家具处理与使用后翻修、首次软包与重新软包分别组织，不为名称相近而合并。

| 指标 | 本轮后 |
|---|---:|
| 当前NACE完整源节点 / 类有说明 | 1047 / 651 |
| 本地分支源节点：ISIC4 / ISIC5 / NACE2 / NACE2.1 | 17 / 18 / 22 / 12 |
| 家具及边界自有节点 / 边 / 根 | 18 / 16 / 2 |
| 导航 / 复用锚点 / 自有活动 | 4 / 2 / 12 |
| 此前家具ID保留 / 本轮新增ID | 11 / 7 |
| 活动四版范围已审 / 仅两套当前体系已审 | 11 / 1 |
| 自有活动→ISIC5绑定：类级 / 组级 | 9 / 3 |
| 已审来源绑定 / 活跃候选 / 候选转换历史 | 52 / 7 / 1 |
| 精确定位证据 / 跨体系研究关系 | 68 / 14 |
| 官方表实例记录独立审查 | 35 |

35条审查按原件实例计数：NACE2.1→2为7、ISIC4→NACE2为9、NACE2→2.1为7、Eurostat XKOS直接桥为9、ISIC4→5材料家具范围为3。反向或重复来源不是新增唯一概念对；三条材料家具审查只批准共同活动相关，2393的完整2026勘误分配没有因此清空。原ISIC专题的605行、161个审查案例和263节点目录仍独立，不改写其旧决定或用另一报告的案例重复抬高全局已审数。

14条Atlas研究关系均为范围限定relatedMatch，保留`official_mapping_id=null`。新310组、维修和安装的关系由两端相同活动直接支持；旧研究关系的额外活动证据带历史追加，不替换原ID。目录QA没有重复、孤儿、自引用或循环。

## 可复现实现、检查与失败

新增`furniture_followup.py`处理SPARQL项、RDF说明组件、原方向反向表、直接XKOS/SKOS及追加审查。`furniture-followup-review.json`绑定原39条审查输入的SHA-256，旧文件不改；新增29条证据、5活动、2导航及21条官方行审查。变动原件、查询、身份或证据字段会使复用决定失效。每条证据保留Unicode区间、字段/片段哈希和原结果行；完整选段在本地，公开UN资料只存定位及自有说明。

```sh
python3 -m pip install -r requirements-isic.txt --target data/local/deps
# 另需Poppler的pdftotext
python3 -m atlas_sources validate
python3 -m atlas_sources collect
python3 -m atlas_sources verify
python3 -m atlas_sources reproduce-furniture
python3 -m atlas_sources reproduce-economy
python3 -m atlas_sources report
python3 -m unittest discover -s tests -v
node scripts/check_furniture_view.js
node scripts/check_economy_view.js
open data/local/economy/furniture/index.html
```

联网仅在collect：按锁重取缺失原件并验证，已有原件读缓存；`--refresh`发现漂移保留旧锁及新旧快照。首次新增资源用`collect --resource <对应ID> --freeze`，不需要对现有锁重新冻结。全部10个新资源ID列在上表，URL、权利和查询文件在注册表。

实测家具从21个锁定原件、manifest、三份研究输入和七份精确查询，在干净目录内无网络重建21/21产物一致；既有ISIC专项35/35一致。原39条家具输入、四份ISIC审查输入、263节点索引和两个原NACE2.1规范化文件与`ecc2611`逐字节无差异。82项测试通过，包含URI/notation区别、说明组件不覆盖、空源Level/G1保真、XKOS发布者谓词、无阳性对照拒绝判无、对应分歧保留、官方活动分配权限、当前部件旧版缺口和身份/历史保留。Python3.10.13、固定Access依赖、Poppler26.04.0、Node22.21.1。

两个页面的离线DOM模拟通过：覆盖组级提示、当前两源待审、旧候选转换历史、独立说明组件、直接审计和46.6冲突。未完成真实浏览器视觉验收，未把DOM模拟称作该验收。

如实记录探索及实现失败：带点号的错误URI返回空结果，改用官方notation验证后的无点URI；前缀广扫超时，改为有界精确图查询；ShowVoc只读查询曾HTTP502，CIRCABC页面读取曾404，未据此声称分类不存在；反向表的空Level及G1导致初次严格解析失败，随后保留原值并补测试；初始“全部代码对必须一致”校验在46.6失败，改为保留两份发布者变体并冻结明确差异审查，不改原件。探索记录见`data/research/furniture-source-observations-20261109.json`。正式10份采集均成功，既有两项权限阻止不变；没有绕过登录、访问限制或使用猜测补节点。

主要输出：原始快照与`data/queries/`、`data/normalized/NACE/Rev.2/`三个新转换、`data/research/furniture-followup-review.json`、`data/atlas/economy/furniture-directory.json`、`data/reports/furniture-alignment.json`与`furniture-reproduction.json`，以及本地说明/证据和浏览页。后续仍需当前版直接官方对应、材料工序细分、旧部件分配及已记录的发布者冲突依据；不将这些未决项强行关闭。
