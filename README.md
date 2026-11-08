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
- [原始分类体系候选清单（机器可读）](data/source-candidates.csv)
- [Codex 项目协作说明](AGENTS.md)

## 当前状态

已在原始 38 条候选之外建立可持续维护的 [50 个来源的结构化登记](data/registry/sources.json)，覆盖 15 个导航领域，并单独保存从 UNSD Family 发现的 149 条候选。核实程度、资料是否下载、是否解析分别记录，未决事实保留为空，不将全部登记称为核实完成。

已实现内容寻址采集、版本/URL/哈希锁定、许可分流、变化检测、源结构解析、QA 和本地来源浏览。真实采集覆盖 6 个来源、16 个文件。基础适配器可解析8个结构资源；经济活动专项另解析两版ISIC完整注释和605行官方对应。O*NET 原始及解析数据依 CC BY 4.0 入库；UNSD完整资料和衍生说明因再分发条件未确认仍留在本地。

ISIC Rev.4 的419个类、Rev.5 的463个类均有官方说明；原始层级、五项Rev.4数据库更正、50项Rev.5注释更新、拆分/合并/转移、部分对应和发布者问号都可追溯。14个案例已研究，形成3个稳定研究概念和6条双向来源关联；完整自有统一目录仍在逐领域整理中。

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
open data/local/economy/isic/index.html
```

未开发现实实体关联或需求理论。后续继续按明确分类对象和合法本地快照逐领域整理，保留原始目录、版本及映射的语义差异。

仓库：<https://github.com/liamamilin/World-Classification-Atlas>
