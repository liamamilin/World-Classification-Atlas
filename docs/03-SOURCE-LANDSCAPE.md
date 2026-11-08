# 全球分类来源地图（发现阶段）

**此表是启动世界分类目录盘点的候选名单，不是已完成采集的官方数据集。** 每一项必须由 Codex 核实最新版本、下载资源、版权与层级。15 领域是导航分组，允许同一标准跨领域。

| 领域 | 源标准候选 | 分类对象及整合提示 |
|---|---|---|
| 01 经济与行业 | ISIC、NAICS、NACE、GB/T 4754 | 经济活动，适合做跨体系映射，注意版本与国家特有分类 |
| 02 产品与服务 | CPC（UN Central Product Classification）、HS、UNSPSC、eCl@ss | 商品/服务/贸易商品与采购品类；范围不同，需部分映射 |
| 03 消费与支出 | COICOP、COFOG、COPNI | 家庭消费目的、政府职能、非营利机构目的，不同对象 |
| 04 学科与知识 | OECD FORD、ISCED-F、LCC、DDC | 科研领域、教育领域、图书馆馆藏知识；不同用途 |
| 05 职业与技能 | ISCO、ESCO、O*NET | 职业、职业画像、技能任务；非完全同类 |
| 06 技术与发明 | IPC、CPC（Cooperative Patent Classification）、ACM CCS | 专利技术/计算学科，不与 UN CPC 混淆 |
| 07 医学与健康 | ICD-11、ICF、ATC、SNOMED CT | 疾病/功能/药物/临床概念，分开分类对象 |
| 08 生物与自然 | Catalogue of Life、GBIF、NCBI Taxonomy | 生物分类群与分类法概念，注意系统发育和同物异名 |
| 09 地理与空间 | UN M49、ISO 3166、地理要素类目（待确定具体标准） | 地区代码和地理实体类别不同 |
| 10 环境与资源 | SEEA、土地覆盖分类（如 FAO LCCS）、能源产品分类 | 环境资产/地表覆盖/能源商品 |
| 11 法律与公共治理 | 法律主题目录（具体官方体系待查）、COFOG | 法律主题与政府职能是不同分类对象 |
| 12 文化与艺术 | Getty AAT、艺术品分类、文化活动分类 | 物品/形式/文化活动，许可尤其重要 |
| 13 教育与培训 | ISCED、ISCED-F、国家专业目录 | 教育层次与教育领域需分别成目录 |
| 14 组织与机构 | SNA institutional sectors、ICNPO、其他官方机构分类 | 机构部门与非营利组织类型 |
| 15 人类活动与生活 | ICATUS、体育活动分类、旅游活动分类 | 时间使用活动、运动、旅游活动 |

## 官方来源发现入口

- [UNSD International Family of Classifications](https://unstats.un.org/unsd/classifications/Family/ListByName)
- [UNSD 国家分类信息](https://unstats.un.org/unsd/classifications/nationalclassifications)
- [Eurostat RAMON](https://ec.europa.eu/eurostat/ramon/)
- [UNSD 分类资源总入口](https://unstats.un.org/unsd/classifications/)
- [WIPO IPC](https://ipcpub.wipo.int/)
- [EPO / USPTO Cooperative Patent Classification](https://www.cooperativepatentclassification.org/)
- [WHO ICD](https://icd.who.int/)
- [WHO ICF](https://www.who.int/standards/classifications/international-classification-of-functioning-disability-and-health)
- [WHO ATC/DDD](https://www.who.int/tools/atc-ddd-toolkit)
- [ESCO](https://esco.ec.europa.eu/)
- [O*NET Resource Center](https://www.onetcenter.org/database.html)
- [GBIF](https://www.gbif.org/)
- [Catalogue of Life](https://www.catalogueoflife.org/)
- [NCBI Taxonomy](https://www.ncbi.nlm.nih.gov/taxonomy)
- [UNESCO UIS ISCED](https://uis.unesco.org/en/topic/international-standard-classification-education-isced)
- [Getty Vocabularies](https://www.getty.edu/research/tools/vocabularies/)
- [UN SEEA](https://seea.un.org/)
- [UN M49](https://unstats.un.org/unsd/methodology/m49/)

## 注意事项

- 不能把 CPC 两个缩写混淆：UN Central Product Classification 与 Cooperative Patent Classification。
- 标准 **latest/edition/发布年份**必须实时核对，不根据名称自行推断。
- UNSD 与 RAMON 是标准发现入口，并非其中每条标准均可免费批量下载。
- 需要为每个标准建立单独的来源事实记录：官方所有者、正确发布地址、可访问资源、结构层级、包含/排除范围、条目数量（仅来自实际数据）、许可与维护状态。
- 若真实下载后发现领域分类过粗或漏掉主要对象，增加领域导航或新目录，但不要制造人为的统一分类理论。
- 同一源标准在多个领域出现，不应重复下载原始文件，可通过多领域关系引用唯一来源记录。
