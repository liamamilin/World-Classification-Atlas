# 来源注册表与可复现采集

工作沿用 README 和 01–06 的最终目标。基础工具覆盖来源发现、证据登记、本地资料与源结构解析；经济活动专项已开始定义/注释、官方对应和已审目录整理，详见09–11历史记录及12边界跟进。没有开发现实实体关系或需求理论。

## 运行

Python 3.10+。基础命令仅使用标准库；可选 `economy` 专项另需 `requirements-isic.txt` 和 Poppler。在仓库根目录运行：

```sh
python3 -m atlas_sources validate
python3 -m atlas_sources discover
python3 -m atlas_sources audit
python3 -m atlas_sources collect
python3 -m atlas_sources normalize
python3 -m atlas_sources verify
python3 -m atlas_sources report
python3 -m unittest discover -s tests -v
open data/reports/registry.html
```

`discover`、`audit`、`collect` 需要访问官方互联网；其余命令离线运行。注册表浏览视图是自包含 HTML，支持按领域、核实状态、名称/对象/机构检索，不需要服务器。文件内不嵌入受限原始数据。当前工具的浏览器策略禁止 `file://`，因此本次做了 HTML 生成与脚本检查，未声称完成浏览器视觉验收。

`discover` 会记录 RAMON 的实测 404 并返回 1，但继续读取可用的 Eurostat 分类入口；`audit` 遇到超时、拒绝或 robots 限制也返回 1，并保存所有其他结果。这些退出码不能解释为整份注册表失效。`collect` 的许可阻止是预期状态，不发出该资源的请求；运输失败或哈希漂移返回 1。`verify` / `normalize` 遇到已允许但未下载的资源或完整性错误返回 1。

只复现公开入库的 O*NET 文件：

```sh
python3 -m atlas_sources collect --resource onet31-occupations --resource onet31-content-model --resource onet2019-taxonomy
```

首次运行已有锁文件的干净检出时，缺失文件会重新下载，并与已提交 SHA-256 核对。后续默认使用缓存并检验哈希；需要实测上游变化时：

```sh
python3 -m atlas_sources collect --refresh
```

新增资源须先审查 `data/registry/resources.json` 的本地处理与再分发条件，再运行 `collect --resource 新资源ID --freeze`。`--freeze` 只锁定尚未有 pin 的资源，不能覆盖已有 pin。上游字节变化时，新旧文件都保留，命令报 `drift`，旧 pin 不变；人工核实修订原因后用新的版本或资源 ID 登记。不要删除 pin 来掩盖变化。

## 三组互不冒充的记录

- `data/source-candidates.csv`：原始 38 条线索，原样保留。
- `data/discovery/unsd-family.json`：由官方 Family 页面解析出的 149 条名称/详情入口，包括没有详情链接的条目，全部仍为候选；页面布局或公布条数不符会报错。
- `data/registry/sources.json`：人工研究的 50 个来源；覆盖全部原候选，新增 BEC、SITC、SIEC、CEP、ICCS、EuroVoc、ISCED-T、ICNP/TSO、Nice、Locarno、EBOPS、ICSE。不能将 149 和 50 相加为不重复来源总数。

每个来源有分类对象、发布者、多领域归属、明确的参考版本集合、层级描述、下载入口、许可各项权利、官方映射入口、核实日期、字段证据和未决问题。未知值使用 `null` / 空版本集合，不用虚构版本。`verified_metadata` 仅指这条登记的元数据已核实，不意味着全量目录已采集。`partially_verified`、`candidate`、`inaccessible` 保留缺口；`link-audit.json` 只是独立的访问观察，HTTP 200 不证明版本、许可或语义正确。

版本中的 `snapshot-*` 是本项目的采集日期标签，不是官方版本号。future / draft / pre-edit 保留在版次状态。一个来源可包含多种分类对象，但真正进入解析时按对象/资源分开。SEEA 登记为包含多个分类的核算框架；`LEGAL_TOPICS` 保留原始占位身份，不能称为已找到的具体标准。

## 文件与权限

```text
data/registry/resources.json                    具体URL、角色、格式、编码、版次与权利
data/resources.lock.json                       来源 + 版本 + URL + SHA-256
data/acquisition/<run>.json                    每次采集的成功、失败、阻止、漂移
data/raw/<source>/<edition>/<resource>/<sha>/   允许再分发的原始字节及manifest
data/local/raw/...                             再分发未确认、仅本地研究的资料
data/normalized/<source>/<edition>/<resource>/<sha>/nodes.jsonl
data/local/normalized/...                      仅本地资料的解析结果
data/reports/                                  实测完整性、覆盖和历史解析失败
```

原始文件不重编码、不修改代码、不注入说明。manifest 保存下载 UTC 时间、请求/最终 URL、响应 MIME、ETag/Last-Modified（服务器提供时）、字节数、原始 SHA-256、语言、资源角色、发布日期（未知为空）、robots 观察与许可依据。文件按内容地址保存；同一内容不覆盖首次 manifest。后续失败的 HTTP 成功载荷也保留用于检查，但不自动写入锁文件。最初 ISIC5 的编码失败发生在失败载荷保留改进前，其错误已留在运行日志，随后以正确编码完整重取。

`.gitattributes` 对 `data/raw/` 禁用 Git 文本换行转换与文本差异；官方 CSV 的 CRLF 原样保留，不能为满足代码空白检查而更改原件。

`data/local/` 被 Git 忽略；当前 UNSD 文件与解析结果只保存在这里。UNSD 页面明确提供结构下载，本地处理采用该下载用途的解释，**没有将它推定成公众再分发许可**。这是待进一步核实的权利边界。UNdata 的开放条款不自动适用于 UNSD 另一个站点。UNSPSC 的下载虽然免费，但本地处理和再分发条件未充分确认，程序阻止；SNOMED 未取得授权，也不会请求下载。完整目录或引用中涉及的商标/数据库许可不能被本项目代码许可覆盖。公开数据署名见 `data/ATTRIBUTION.md`。

执行结果与逐领域比较见 `08-EXECUTION-REPORT-2026-11-08.md`，对比统计随 `report` 命令从原文件重新计算。

下载按顺序限速，读取 robots、使用超时、仅对暂时性错误有限重试，不绕过登录/CAPTCHA。单文件上限 50 MiB；大型分类群归档需后续实现流式适配器，本轮没有将发生记录、基因序列或现实物种个体混入分类资料。

## 源节点与检查边界

节点身份至少是 `source_id + edition + resource_id + code`；多个语义不同的文件不可因同码直接合并。节点保留代码字符串、原标签、定义及来源类型、父级列表、原始行/字段或原始 JSON-LD 对象、原文件哈希。ISIC经济活动局部目录已有110个类范围锚点、30个自有活动子节点和123个仅导航上级，之前身份保留；原目录仍独立保存。仅当前版已审、待审旧来源和待审目录提案分别标记，产品目录只作旁证。

CSV、定宽文本和 CTDL JSON-LD 使用显式适配器；不猜测不认识的表头。ISIC 数字代码的长度与所在 section 的原始顺序、CPC 前缀、COFOG/COPNI 点号及 O*NET 内容模型点号用于重建父级，并明确标记派生方式。定义缺失保留为空，不让模型补写。没有父级字段的职业文件保留平表，不能因为 QA 显示一层就声称官方职业分类只有一层。

QA 检查全部解析条目、重复码、孤儿、自引用、循环、多父级、深度、叶子、定义覆盖和已知发布方条数。O*NET 两份 CSV 与官方页面的 1,016 / 3,006 行对照通过；UNSD 未独立确认发布方统计值，保持 `publisher_count_match: null`。源文件不提供的废止/别名状态标为未提供。遇到结构失败不输出部分“成功目录”，原始文件保留，失败信息在 `reports/rejected/`。该目录包含已经修复的历史表头失败，不代表当前仍失败。

通用 `verify` 对 XLSX 检查 ZIP/OOXML 容器；`economy` 专项已经完整解析ISIC两版说明与605行官方对应，保留GSIM、问号和原始单元格，覆盖结果由 `report` 的专项字段展示。ICATUS 未确认版次的旧文件仍只做编码检查，不纳入2016节点统计。CTDL 是明确的 O*NET-SOC2019 集合，含自身 `dateModified=2025-01-16`，所以与数据库 31.0 分版本保存；首次采集记录的组织路径在初次代码提交前已更正，原始字节不变，manifest 含更正说明。

## 逐领域继续研究的依据

经济活动已完成两版ISIC的定义/注释补采和官方类级对应解析，接续审查 partial/split/merge、后续勘误和待审概念，再核对 NAICS/NACE 等同对象来源。对应表解析成功还不等于全部映射已审定。职业代码与技能/工作内容模型另成目录；COFOG 与 COPNI 即使都涉及支出也不合并。其他领域的版权、完整资料和细粒度层级仍有明确缺口，详见覆盖报告，不能因为当前采集方便就认定这些领域已经完成。

经济活动扩展审查及离线重建：

```sh
python3 -m pip install -r requirements-isic.txt --target data/local/deps
python3 -m atlas_sources economy
python3 -m atlas_sources reproduce-economy
node scripts/check_economy_view.js
```

`reproduce-economy`先验证基线，再在无任何既有派生结果的临时目录内，仅用锁定原件、manifest和四份审查输入重建，比较全部35个专项输出的SHA-256，写`data/reports/isic-reproduction.json`。临时目录退出后删除；不联网，不复制既有派生结果。使用同一Python/Access/Poppler环境；这验证相同环境的确定性，不表示任意依赖版本都逐字节相同。`check_economy_view.js`为生成HTML的离线DOM模拟，不声称浏览器视觉验收。

家具分支新增NACE接入及同对象研究，详见[13](13-FURNITURE-MULTISOURCE-ALIGNMENT.md)。`furniture`从11个锁定原件重建，不依赖已有ISIC派生文件；`reproduce-furniture`现复制21个锁定原件、manifest、锁、三份研究输入及七份精确SPARQL查询，在新临时目录中比较21个产物。初次15个产物的历史结果仍见13；后续见[14](14-FURNITURE-OFFICIAL-EVIDENCE-FOLLOWUPS.md)。`data/normalized/NACE/`按Eurostat许可公开保存转换后的源结构和对应，完整PDF因第三方封面例外继续本地保存。当前目录探索分别见两个本地HTML；没有用家具目录替换263节点的既有ISIC研究目录。

家具跟进采用追加的`data/research/furniture-followup-review.json`，绑定初次39条证据审查输入的原始SHA-256；不覆盖旧决定。旧NACE的RDF说明与2008手册分组件保存，官方XKOS/SKOS语义与Atlas有界判断分开。`data/queries/`是实际URL中query参数的精确文本，哈希或URL不一致、带截断/外部联邦查询、缺阳性对照都会使审计失败。零行只表示在明确定义的官方图快照中未观察到关系，不是发布者的无对应声明。
