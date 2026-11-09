# World Classification Atlas

> 以真实世界已经存在的分类目录为起点，建立一个可追溯、可整理、可融合、可逐层探索的世界分类图谱。

## 项目定位

World Classification Atlas（世界分类图谱）不是从零凭空创造一套“世界万物理论”，而是系统发现各类**现有分类体系**，将其原始结构与说明资料保存到本地，按照**领域和实际分类对象**逐一研究，最终形成我们自己的多层级分类目录，并保留到各来源标准的关联。

## 工作顺序

1. **全球分类目录盘点**：识别各领域已有的分类标准、管理机构、分类对象、版本、层级、获取方式和许可。
2. **来源资料本地化**：下载可合法获取的原始分类结构、代码表、定义、说明手册、版本信息与对照表；保留原始文件、校验和与来源。
3. **按领域整理与融合**：一个领域一个领域处理；相同分类对象的目录比较、映射、合并或细化；不同分类对象保留独立目录。
4. **建设自有统一目录**：形成领域 → 自有目录 → 一级/二级/三级/…/叶子结构；每个节点有稳定身份和原始来源对应。
5. **构建可探索的 Atlas**：浏览、检索、展开层级、查看定义、比较来源、检查未处理覆盖与变更历史。

以上是最终方案中的工作依赖关系，不是反复推翻目标的“版本规划”。

## 明确边界

- **现在仅做分类体系**；暂时不关联现实商品、企业、机构、人物、具体物种实例等现实对象。
- **现在不预设九类需求理论**，也不以需求分类决定世界目录结构。
- 15 个领域是用来盘点分类来源的导航分组，**不是已经确立的世界统一本体**；跨领域分类可以多重归属。
- 不强迫全部目录合成一棵树：不同分类对象（例如疾病、药物、身体功能）应保留独立目录。
- 不以同名或向量相似度作为自动合并的充分条件。
- 没有原始资料、许可或对应依据时，明确保留“待核实”，不虚构来源、节点或映射。

## 项目文档

- [目标和范围](docs/01-PRODUCT-SCOPE.md)
- [完整工作方案与验收](docs/02-WORK-PLAN.md)
- [15 个领域与分类来源入口](docs/03-SOURCE-LANDSCAPE.md)
- [本地采集、版权与可复现性](docs/04-ACQUISITION.md)
- [跨目录整理与融合原则](docs/05-CONSOLIDATION.md)
- [给 Codex 的接续任务](docs/06-CODEX-HANDOFF.md)
- [来源注册表、采集工具与复现命令](docs/07-REGISTRY-AND-REPRODUCTION.md)
- [实测采集与领域覆盖](data/reports/coverage.md)
- [2026-11-08 执行记录、失败与未决问题](docs/08-EXECUTION-REPORT-2026-11-08.md)
- [ISIC 定义、注释、官方对应与经济活动研究](docs/09-ISIC-ECONOMIC-ACTIVITIES.md)
- [ISIC 拆分、合并、2026 勘误审查与目录扩展实测](docs/10-ISIC-REVIEW-AND-DIRECTORY.md)
- [植物奶、食用冰、纺织和核燃料的条款核查与补充对应](docs/11-ISIC-PRIORITY-ALLOCATIONS.md)
- [水冰、口罩、碳织物的旧版边界与竞争来源核查](docs/12-ISIC-BOUNDARY-FOLLOWUPS.md)
- [家具制造：NACE与ISIC同对象多源整理](docs/13-FURNITURE-MULTISOURCE-ALIGNMENT.md)
- [家具表面处理、旧陶瓷家具与直接官方对应跟进](docs/14-FURNITURE-OFFICIAL-EVIDENCE-FOLLOWUPS.md)
- [家具材料细类、旧部件与卫生洁具对应核查](docs/15-FURNITURE-MATERIAL-BOUNDARIES.md)
- [独立承包处理、旧木制部件与官方修订复查](docs/16-FURNITURE-CONTRACT-PARTS-RECHECK.md)
- [原始分类体系候选清单（机器可读）](data/source-candidates.csv)
- [Codex 项目协作说明](AGENTS.md)

## 当前状态

已在原始 38 条候选之外建立可持续维护的 [52 个来源的结构化登记](data/registry/sources.json)，覆盖 15 个导航领域，并单独保存从 UNSD Family 发现的 149 条候选。核实程度、资料是否下载、是否解析分别记录，未决事实保留为空，不将全部登记称为核实完成。

已实现内容寻址采集、版本/URL/哈希锁定、许可分流、变化检测、源结构解析、QA 和本地来源浏览。真实采集覆盖 9 个来源、45 个文件，登记47个资源任务。基础适配器可解析8个结构资源。经济活动专项另解析两版ISIC完整注释和605行官方对应，并选取CPC产品说明作边界旁证。O*NET 原始及解析数据依 CC BY 4.0 入库。UNSD完整资料和衍生说明因再分发条件未确认仍留在本地。

ISIC Rev.4 的419个类、Rev.5 的463个类均有官方说明；原始层级、五项Rev.4数据库更正、50项Rev.5注释更新、拆分/合并/转移、部分对应和发布者问号都可追溯。现有161条官方对应行的逐条审查记录，其中141条批准当前关系、20条审后暂缓，其余444条保留待审。已审关系含107条相关、22条窄向、9条宽向和3条等价。另有6条独立的Atlas活动证据补充关系和2条待审补充候选，未修改605行官方表。

自有经济活动局部目录有110个Rev.5类范围锚点、30个Atlas自有活动子节点、123个来源骨架导航上级，共263节点，先前248个身份保留。130条可回定位的证据支持范围限定研究。3个口罩活动仅审定当前版，7条待审来源关联有独立反查，1个水冰目录提案不计入已审节点。21项问题记录保留历史：1项研究澄清、2项已给研究补充但官方缺口仍在、4项部分处理、14项待审。4处原文差异仍保留。

```sh
python3 -m atlas_sources validate
python3 -m atlas_sources collect
python3 -m atlas_sources normalize
python3 -m atlas_sources report
python3 -m unittest discover -s tests -v
open data/reports/registry.html
```

经济活动专项复现（固定依赖和 Poppler 说明见上方研究文档）：

```sh
python3 -m pip install -r requirements-isic.txt --target data/local/deps
python3 -m atlas_sources economy
python3 -m atlas_sources reproduce-economy
node scripts/check_economy_view.js
open data/local/economy/isic/index.html
```

家具活动已接入NACE两版，与ISIC两版逐条比较。当前NACE完整结构1047节点及原有1598行对应保留；又采到实际反向1598行表和996条Eurostat NACE2→ISIC4直接XKOS对应，发布者closeMatch原样保留。后者与UNSD有995对代码事实一致，46.6→466/465的差异独立记录。当前NACE2.1–ISIC5的命名图审计有1047节点阳性对照，未观察到直接关系；没有通过版本链制造官方等价。

家具及边界研究目录有29节点（6导航、2复用锚点、21活动），上一轮24个身份全部保留。54条官方行已有范围审查，另有23条活动研究关系、141条证据、87条已审绑定和9条待审绑定。新制家用活动家具承包涂装、未成形木料防腐、通用金属工件漆涂层与其他家用木制家具部件独立制造各有活动节点。复查三处官方发布入口与七份已锁定文件，三份表中的卫生洁具对应缺行仍在。旧 NACE 31.01 与31.09的冲突、专用店铺内置部件的旧ISIC候选及46.6来源差异分别保留。263节点ISIC目录继续单独保存。

```sh
python3 -m atlas_sources furniture
python3 -m atlas_sources reproduce-furniture
node scripts/check_furniture_view.js
open data/local/economy/furniture/index.html
```

未开发现实实体关联或需求理论。后续继续按明确分类对象和合法本地快照逐领域整理，保留原始目录、版本及映射的语义差异。

仓库：<https://github.com/liamamilin/World-Classification-Atlas>
