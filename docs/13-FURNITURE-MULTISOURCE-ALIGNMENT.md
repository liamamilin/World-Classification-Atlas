# 家具制造：NACE与ISIC两版的多源整理实测

本轮遵循Goal Anchor的校准方向，从独立的同对象经济活动分类NACE接入家具分支。核实版次、许可和官方对应后再建立范围限定的自有活动。原有263节点ISIC研究目录、605行官方跨版对应及其稳定ID、审查历史和未决问题保持独立；家具研究目录复用其中两个身份，另增九个身份。没有关联现实实体或引入需求理论。

## 版次、许可与官方入口

- [Eurostat NACE官方说明](https://ec.europa.eu/eurostat/web/nace/overview)确认当前分类为Rev.2.1，自2025年起用于欧洲统计；Rev.2用于2008–2024参考期。**2026是手册出版年，不是新的分类revision**。
- [2026手册](https://ec.europa.eu/eurostat/web/products-manuals-and-guidelines/w/ks-01-26-047)于2026-09-17发布，稿件完成于2026年7月，DOI [10.2785/3034037](https://data.europa.eu/doi/10.2785/3034037)。解析430物理页。Rev.2的[2008手册](https://ec.europa.eu/eurostat/web/products-manuals-and-guidelines/-/ks-ra-07-015)解析369物理页，保留原版范围。
- [Eurostat复用条款](https://ec.europa.eu/eurostat/help/copyright-notice)允许署名复用其元数据、出版物和分发工具；修改须明确。2026手册物理第4页明确文本CC BY 4.0，同时第三方封面图片例外。完整PDF留在本地；公开原始工作簿、下载清单、许可页面和结构转换，未抽取或发布第三方图像。UNSD资料仍沿用本地限制，不能把EU许可移给UN文件。署名及非官方修改说明见[data/ATTRIBUTION.md](../data/ATTRIBUTION.md)。
- [官方对应入口](https://ec.europa.eu/eurostat/web/nace/correspondence-tables)链接ShowVoc公开下载页。实际下载清单给出Rev.2.1说明XLSX及**Rev.2.1→Rev.2**对应XLSX；上传时间分别是2026-09-30与2026-09-29，均只是分发组件时间。文件未显式提供表版本号，不因手册提及Version 1.06而给下载文件擅加版本号。
- [UNSD经济分类入口](https://unstats.un.org/unsd/classifications/Econ)提供[ISIC4→NACE2原表](https://unstats.un.org/unsd/classifications/Econ/tables/ISIC/ISIC4_NACE2/ISIC4_NACE2.txt)及[更改历史](https://unstats.un.org/unsd/classifications/Econ/tables/ISIC/ISIC4_NACE2/Change%20history.txt)。历史注明2011-12-09调整46.6等组级链接，并明确类级链接未变；不将其描述为家具修订。

已核查的Eurostat页面、ShowVoc下载清单和UNSD入口中，未发现NACE Rev.2.1→ISIC Rev.5的直接官方表。这是具体入口的观察，不宣称官方永远没有此表。NACE跨版、旧NACE/ISIC和ISIC跨版各自保存；它们的连接路径**没有被传递成官方直接对应或概念等价**。

## 真实采集与完整解析

8个新增资源全部实得，原字节、manifest、URL、UTC时间、robots结果和SHA-256保留。全项目现为50来源、15导航领域、30采集任务、28个锁定文件、7个实得来源；UNSPSC/SNOMED两项许可阻止沿用，未发下载请求。公开数据与仅本地资料分别存放。

| 新原件 | 字节 | SHA-256 |
|---|---:|---|
| nace21-download-list | 3,812 | `9ac085205d2af56b0347b7ab1c65550920af6979f5ec3f9900afb6a98b044698` |
| nace21-notes-20260930 | 211,513 | `9a0e11d53c97475b5a7b132cdbf1fdf4b13e3d584402a04c3f5455dcc3e06442` |
| nace21-nace2-correspondence | 204,677 | `2ceee6c855731842c7933a897a9400756fe23c4416b00176631236053b704ac2` |
| nace21-manual-2026 | 8,613,519 | `3cd7bc5d1dcc60c3e0ecaefa732ad2d30d87d009abf5b1b823632e12a8dd0cd4` |
| nace2-manual-2008 | 5,908,141 | `452982566cfcb4ee4f0e20d19395cb9c81726828b3bce48fdf4a0c7efc3a2302` |
| nace-reuse-policy | 177,790 | `87324bd393d88bd5c69652e73eec8791e966935fbf92a2b01054a2b5b7d67d26` |
| isic4-nace2-correspondence | 18,838 | `fd5283a539afecfb36aad2ad3023787c333a133458463592d681c30d1a15a101` |
| isic4-nace2-change-history | 242 | `94d6fa07aae5795c9a7604712d83283ad7398cd04716c1147549e3d61c1c847f` |

NACE Rev.2.1说明工作簿完整解析1047节点，四层为22/87/287/651；所有651个类有独立说明，总体861节点有说明，其余为空，不补写定义。原始ID列、代码中的点号/前导零、Level/Section、包含、补充包含、排除及Implementation_Rule独立保留。父级按明确列与代码格式重建，QA没有重复、孤儿、自引用或循环。

NACE跨版表保留1598个原始行，其中四层对应行47/150/426/975；不能把975行称为975个类。完整图与NumberOfCorresponding_NACE2列相符。46.89一行明示无旧对应，目标保留`null`，不是删行或虚构旧代码。ISIC4→NACE2表保留996行，包含原始`ISIC4part`/`NACE2part`的0/1标志、行号和方向；不转成比例，也不以标志自动批准包含或等价。所有分配权重为空。

旧NACE只从2008手册提取家具分支、三项材料转入类及祖先，共14节点、7类，物理页114、151–155、193–194可回查。C只提取标题，不宣称完整旧体系或完整C定义。用于本地浏览的四版分支共37源节点：ISIC4为9、ISIC5为10、NACE2为14、NACE2.1为4；与完整当前NACE结构的1047节点分开计数。

## 家具分支逐项研究

NACE2.1的31.00覆盖任意材料家具，并明确包括石、混凝土、陶瓷家具；ISIC4的3100及ISIC5的3101/3102均排这三种材料到2393/2395/2396。因此不能把NACE31.00等同于ISIC5两个家具类的并集。

官方NACE表的31.00有**七个旧类**：旧31.01、31.02、31.03、31.09，以及23.42、23.69、23.70。前三个材料类只是家具活动转入，不是整个卫生洁具、混凝土制品或石加工类合并。原表方向31.00→各旧类、Common_Content、TypeOfMapping、TypeOfCorrespondence和全部七行均保留；14条独立审查覆盖这七行，以及ISIC4→旧NACE对应的七行。审查仅批准范围限定的`relatedMatch`，未批准整类等价。

现有ISIC4的3100→ISIC5的3101/3102两行继续保留官方RC4.1分解、原行187/188和原表版本。2026家具类及其祖先没有注释更新；材料2393有更新，本轮仅核查其明确陶瓷家具活动，不据此清空2393的整类勘误待审。

7个Atlas有界活动如下，均为制造活动而非产品实例，均保留同对象的来源包含证据：

| 自有活动 | ISIC Rev.4 | ISIC Rev.5 | NACE Rev.2（2008） | NACE Rev.2.1 |
|---|---|---|---|---|
| 木制厨房家具制造 | 3100 | 3101 | 31.02 | 31.00 |
| 金属办公家具制造 | 3100 | 3102 | 31.01 | 31.00 |
| 弹簧床垫制造 | 3100 | 3102 | 31.03 | 31.00 |
| 塑料花园座椅制造 | 3100 | 3102 | 31.09 | 31.00 |
| 陶瓷家具制造 | 2393 | 2393 | 23.42 **待审** | 31.00 |
| 混凝土家具制造 | 2395 | 2395 | 23.69 | 31.00 |
| 石制家具制造 | 2396 | 2396 | 23.70 | 31.00 |

活动→来源的`broadMatch`表示来源类比活动更宽。木框架/无框架主要材料的木制规则、竹与木质材料、床垫例外分别依据ISIC5原文；床垫不因床框架材料而改派木制家具。七个范围都排除相关的现场安装、维修或非家具板材，不能把有界活动提升为整个来源类。

9条ISIC类→NACE31.00研究关系分别由两端共享活动支持：旧3100、新3101/3102，以及两版各自2393/2395/2396。均标`origin=atlas_research`、`official_mapping_id=null`、`relatedMatch`，与14条官方行审查分别计数。每个NACE家具叶类和ISIC家具叶类都有已审活动覆盖，**不代表整个类全部范围已审或全表融合完成**。

## 稳定身份、自有路径与证据

家具目录有11节点、10边，层级1/3/7：两个Atlas导航、两个复用类范围锚点、七个自有活动。复用木制/其他家具锚点的原ID，保留既有目录引用与原父级；新ID按显式稳定键登记。家具目录的`parents`只适用于这个scheme，原ISIC路径及263节点目录不被重新挂接或覆盖。新节点九个，不能把两个目录节点数直接相加。

公开索引含33条已审来源绑定、1条单列候选绑定及双向反查。39条证据保存文档身份、字段、Unicode起止区间、整字段/选段哈希、原文件哈希、工作表/行或PDF物理页。本地档案保留选段原文；改变已审原件、身份登记或证据字段即失败。中文活动范围及审查者明确为Atlas/Codex，不冒称官方译文、子码或发布者审批。

## 五项未决问题

1. `FURN-DIRECT-CROSSWALK`：直接NACE2.1–ISIC5官方表未在核查入口找到，保留开放。现有活动证据不替代官方表。
2. `FURN-FINISHING`：当前对应表31.00→旧31.01列家具表面处理，2008手册却在31.09包含该活动。两份来源并存，未建该活动跨版已审子节点，也未批准整类关系。
3. `FURN-CERAMIC-OLD`：旧31.09排除和当前对应表指向23.42，但旧23.42说明只直接列卫生洁具及其他陶瓷装置，未明确陶瓷家具。UNSD旧对应2393→NACE23.42同时存在旧ISIC2393排卫生洁具到2392的范围差异。当前ISIC5的2393已包括卫生洁具，不能倒写旧版。陶瓷家具在两版ISIC和当前NACE的绑定可审，旧NACE绑定仍待审；问题部分处理。
4. `FURN-NACE-ISIC-GENERALITY`：2026手册通用说明称两者前两级相同，但家具实际材料边界跨31/23分支。按具体条款保留差异，继续寻找家具特例的官方解释。
5. `FURN-PARTS-RESIDUAL`：完整家具类的板材/部件、表面处理及用途剩余范围未全部审定。当前七个活动只覆盖明确范围，保留待审。

上述五项为四项open、一项partially_addressed。没有获得发布者答复，也未发送对外信息；既有ISIC水冰、口罩和碳织物等待审历史不在此轮关闭。

## 复现与实测

Python3.10.13、固定Access依赖、Poppler26.04.0；Node v22.21.1用于DOM模拟。在仓库根目录：

```sh
python3 -m pip install -r requirements-isic.txt --target data/local/deps
# 另需Poppler的pdftotext
python3 -m atlas_sources validate
python3 -m atlas_sources collect
python3 -m atlas_sources verify
python3 -m atlas_sources reproduce-economy
python3 -m atlas_sources reproduce-furniture
python3 -m atlas_sources report
python3 -m unittest discover -s tests -v
node scripts/check_economy_view.js
node scripts/check_furniture_view.js
open data/local/economy/furniture/index.html
```

`collect`联网，缺失缓存按已提交锁下载，已存在的缓存按哈希检查。`--refresh`发现漂移时保留旧锁及新旧字节；不承诺未来URL永不变化。其余处理离线。新增资源的首次冻结命令是`collect --resource <8个新资源ID逐个重复> --freeze`，具体URL/ID在资源注册表；重现现有锁不需要重设pin。

实测：家具干净重建15/15产物一致，只复制11个锁定原件/manifest、锁和两份研究输入，不复制既有派生结果；既有ISIC专项35/35一致。71项测试通过，覆盖点号/前导零、原ID与行号、无对应空端点、partial标志、证据变动失效、活动不能冒充整类、两版证据、官方/研究区别、旧NACE候选与稳定身份。两个本地页面的DOM模拟均通过；**未完成真实浏览器视觉验收**。不同PDF提取器版本可能改变布局哈希，应重新审查，不能自动沿用证据。

新页面支持四版源分支及自有树、名称/代码/定义检索、定义原字段、双向来源反查、逐条证据和官方/Atlas研究分栏。它是有界分支的探索结果，尚未汇聚成全领域Atlas入口。

探索与实现失败如实保留：旧copyright路径404，改由官方当前版权页核实；ShowVoc静态网页读取不到数据，公开客户端声明的Download服务可取官方资源，初次Storage/list请求的目录参数无效，未作数据源使用；首个完整表解析因46.89空旧端点失败，现保留发布者明确无对应行并加回归检查。首轮新增测试少填resource_id导致夹具错误，补全后71项通过。实际8项受控采集全部成功，没有绕过登录或限制；没有吞掉原始空端点或用猜测补码。

关键产物：`data/research/furniture-review.json`（审查输入）、`data/atlas/economy/furniture-directory.json`（自有目录/证据/双向绑定）、`data/normalized/NACE/Rev.2.1/`（可署名再用源结构及对应）、`data/reports/furniture-alignment.json`与`furniture-reproduction.json`（实测）、`data/local/economy/furniture/`（完整本地档案与视图）。
