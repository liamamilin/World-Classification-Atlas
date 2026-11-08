# 来源与采集覆盖

核查日期：2026-11-08。来源核实与下载状态独立。

登记 50 个来源；覆盖 15 个导航领域。UNSD Family 独立发现 149 条候选，未经逐条核实，不能与注册表相加。

22 个采集任务，20 个已锁定且通过格式检查，涉及 6 个来源；8 个资源可解析。

| 领域 | 登记 | 有本地文件的来源 | 已解析的来源 |
|---|---:|---:|---:|
| 01-economy 经济与行业 | 5 | 1 | 1 |
| 02-products 产品与服务 | 9 | 1 | 1 |
| 03-consumption 消费与支出 | 4 | 2 | 2 |
| 04-knowledge 学科与知识 | 6 | 0 | 0 |
| 05-occupations 职业与技能 | 4 | 1 | 1 |
| 06-technology 技术与发明 | 5 | 0 | 0 |
| 07-health 医学与健康 | 4 | 0 | 0 |
| 08-biodiversity 生物与自然 | 3 | 0 | 0 |
| 09-geography 地理与空间 | 2 | 0 | 0 |
| 10-environment 环境与资源 | 4 | 0 | 0 |
| 11-governance 法律与公共治理 | 4 | 1 | 1 |
| 12-culture 文化与艺术 | 2 | 0 | 0 |
| 13-education 教育与培训 | 4 | 0 | 0 |
| 14-organizations 组织与机构 | 4 | 1 | 1 |
| 15-activities 人类活动与生活 | 2 | 1 | 0 |

## 文件实测

| 资源 | 版本 | 状态 | 节点/层级分布 | 定义 |
|---|---|---|---|---:|
| isic4-structure | Rev.4 | parsed | 766 / {1: 21, 2: 88, 3: 238, 4: 419} | 0 |
| isic5-structure | Rev.5 | parsed | 830 / {1: 22, 2: 87, 3: 258, 4: 463} | 0 |
| cpc3-structure | 3.0 | parsed | 4586 / {1: 10, 2: 71, 3: 327, 4: 1301, 5: 2877} | 0 |
| cofog1999-structure | 1999 | parsed | 188 / {1: 10, 2: 69, 3: 109} | 0 |
| copni1999-structure | 1999 | parsed | 65 / {1: 9, 2: 26, 3: 30} | 0 |
| icatus-portal-structure | portal-undated | format_checked_only | 未统计 | — |
| isic4-isic5-correspondence | Rev.5 | format_checked_only; economy: {'status': 'correspondence_parsed', 'rows': 605} | 未统计 | — |
| onet31-occupations | 31.0 | parsed | 1016 / {1: 1016} | 1016 |
| onet31-content-model | 31.0 | parsed | 3006 / {1: 6, 2: 18, 3: 70, 4: 333, 5: 121, 6: 371, 7: 2087} | 587 |
| onet2019-taxonomy | SOC2019-snapshot-2026-11-08 | parsed | 1016 / {1: 1016} | 1016 |
| unspsc-current-workbook | unverified-version | blocked_rights | 未统计 | — |
| snomed-international | authorization-required | blocked_rights | 未统计 | — |
| isic4-manual-2008 | Rev.4 | format_checked_only; economy: {'status': 'text_extracted', 'pages': 307} | 未统计 | — |
| isic4-database | Rev.4 | format_checked_only; economy: {'status': 'notes_parsed', 'nodes': 766} | 未统计 | — |
| isic5-notes-20260819 | Rev.5 | format_checked_only; economy: {'status': 'notes_parsed', 'nodes': 830} | 未统计 | — |
| isic5-white-cover-2026 | Rev.5 | format_checked_only; economy: {'status': 'text_extracted', 'pages': 335} | 未统计 | — |
| isic5-errata-2026 | Rev.5 | format_checked_only; economy: {'status': 'text_extracted', 'pages': 66} | 未统计 | — |
| isic4-isic5-technical-note-20241025 | Rev.5 | format_checked_only; economy: {'status': 'text_extracted', 'pages': 1} | 未统计 | — |
| cpc21-manual-2015 | 2.1 | format_checked_only; economy: {'status': 'text_extracted', 'pages': 618} | 未统计 | — |
| cpc3-notes-20250630 | 3.0 | format_checked_only; economy: {'status': 'text_extracted', 'pages': 534} | 未统计 | — |
| cpc21-readme-20250403 | 2.1 | format_checked_only; economy: {'status': 'text_extracted', 'pages': 1} | 未统计 | — |
| cpc21-notes-20250403 | 2.1 | format_checked_only; economy: {'status': 'selected_auxiliary_product_evidence', 'main_sheet_code_rows': 4144, 'selected_subclasses': 7, 'trade_template_rows_not_expanded': 72, 'use': 'auxiliary product evidence; not an economic-activity scheme or equivalence'} | 未统计 | — |

经济活动专项结果另见 [ISIC 实测报告](isic-economy.json)：包含完整注释解析、官方对应表及已审研究概念。上表 status 为通用格式/结构检查，economy 字段表示专项处理。

经济活动局部目录：110 个已审类范围锚点、123 个仅作导航的上级；141 条已审当前关系。所有605行仍保留原始版本和审查队列，详见 [扩展审查](isic-expanded-review.json)。上级导航不计作已审语义覆盖。

植物奶/食用冰/纺织/核燃料专项：30 个Atlas自有活动子节点，18 条官方行的活动范围审查；另有6 条已审研究补充和2 条待审研究候选。补充关系独立于官方表，见 [优先问题证据报告](isic-priority-review.json)。

其中3个活动只审定Rev.5当前范围；7条待审来源关联与已审绑定分别索引，1个待审目录提案不计入已审节点。CPC产品说明和主要行业对应仅作旁证，见 [边界核查](isic-boundary-review.json)。

节点数按实际原文件统计，不能跨表累加为世界概念总量。O*NET 两种职业资源包含重复代码；职业文件不提供父子边，未据代码补造缺失父节点。

## 未决项（逐来源）

- ISIC: 再分发适用条款待逐文件确认。 [官方入口](https://unstats.un.org/unsd/classifications/econ/)
- NAICS: 公开再分发许可待核实。 [官方入口](https://www.census.gov/naics/)
- NACE: 公开再分发许可待核实。 [官方入口](https://ec.europa.eu/eurostat/web/nace/)
- GBT4754: 公开再分发许可待核实；官方映射及精确端点版本待核实。 [官方入口](https://www.stats.gov.cn/sj/tjbz/gjtjbz/202302/t20230213_1902779.html)
- UN_CPC: 再分发适用条款待逐文件确认。 [官方入口](https://unstats.un.org/unsd/classifications/econ/)
- HS: 公开再分发许可待核实。 [官方入口](https://www.wcoomd.org/en/topics/nomenclature/instrument-and-tools/hs-nomenclature-2028-edition/correlation-tables-hs-2022-2028.aspx)
- UNSPSC: 公开再分发许可待核实；官方映射及精确端点版本待核实；明确版本待核实；五层名称及可选层级需核查原文件。 [官方入口](https://www.undp.org/unspsc)
- ECLASS: 官方映射及精确端点版本待核实；原始层级待文件或手册核实。 [官方入口](https://eclass.eu/en/eclass-standard/releases)
- COICOP: 再分发适用条款待逐文件确认。 [官方入口](https://unstats.un.org/unsd/classifications/econ/)
- COFOG: 官方映射及精确端点版本待核实；再分发适用条款待逐文件确认。 [官方入口](https://unstats.un.org/unsd/classifications/econ/)
- COPNI: 官方映射及精确端点版本待核实；再分发适用条款待逐文件确认。 [官方入口](https://unstats.un.org/unsd/classifications/econ/)
- FORD: 公开再分发许可待核实；官方映射及精确端点版本待核实。 [官方入口](https://unstats.un.org/unsd/classifications/Family/Detail/1039)
- ISCED_F: 公开再分发许可待核实。 [官方入口](https://www.uis.unesco.org/en/methods-and-tools/isced)
- LCC: 公开再分发许可待核实；官方映射及精确端点版本待核实；明确版本待核实；原始层级待文件或手册核实。 [官方入口](https://www.loc.gov/catdir/cpso/lcco/)
- DDC: 官方映射及精确端点版本待核实；原始层级待文件或手册核实。 [官方入口](https://help.oclc.org/Metadata_Services/WebDewey/WebDewey_user_guide/Get_started_with_WebDewey/About_WebDewey)
- ISCO: 公开再分发许可待核实。 [官方入口](https://www.ilo.org/publications/international-standard-classification-occupations-2008-isco-08-structure)
- ESCO: 公开再分发许可待核实；原始层级待文件或手册核实。 [官方入口](https://esco.ec.europa.eu/en/use-esco/download)
- IPC: 公开再分发许可待核实。 [官方入口](https://www.wipo.int/en/web/classification-ipc)
- PATENT_CPC: 公开再分发许可待核实；原始层级待文件或手册核实。 [官方入口](https://www.cooperativepatentclassification.org/cpcSchemeAndDefinitions/bulk)
- ACM_CCS: 公开再分发许可待核实；官方映射及精确端点版本待核实；明确版本待核实；原始层级待文件或手册核实。 [官方入口](https://dl.acm.org/ccs)
- ICD11: 官方映射及精确端点版本待核实；原始层级待文件或手册核实；再分发适用条款待逐文件确认。 [官方入口](https://icd.who.int/browse/2026-01/mms/en)
- ICF: 公开再分发许可待核实；官方映射及精确端点版本待核实；原始层级待文件或手册核实。 [官方入口](https://www.who.int/standards/classifications/international-classification-of-functioning-disability-and-health)
- ATC: 官方映射及精确端点版本待核实；再分发适用条款待逐文件确认。 [官方入口](https://atcddd.fhi.no/atc_ddd_index/)
- SNOMED: 官方映射及精确端点版本待核实；明确版本待核实；原始层级待文件或手册核实。 [官方入口](https://www.snomed.org/get-snomed)
- COL: 公开再分发许可待核实；官方映射及精确端点版本待核实。 [官方入口](https://www.catalogueoflife.org/data/download)
- GBIF: 公开再分发许可待核实；官方映射及精确端点版本待核实；明确版本待核实；原始层级待文件或手册核实。 [官方入口](https://www.gbif.org/dataset/d7dddbf4-2cf0-4f39-9b2a-bb099caae36c)
- NCBI_TAX: 公开再分发许可待核实；官方映射及精确端点版本待核实；明确版本待核实。 [官方入口](https://ftp.ncbi.nlm.nih.gov/pub/taxonomy/)
- M49: 公开再分发许可待核实。 [官方入口](https://unstats.un.org/unsd/methodology/m49/)
- ISO3166: 官方映射及精确端点版本待核实；原始层级待文件或手册核实。 [官方入口](https://www.iso.org/iso-3166-country-codes.html)
- SEEA: 公开再分发许可待核实；官方映射及精确端点版本待核实；原始层级待文件或手册核实；framework_only：不得将整部手册直接解析为一个分类树。 [官方入口](https://seea.un.org/content/seea-central-framework)
- FAO_LCCS: 公开再分发许可待核实；官方映射及精确端点版本待核实；原始层级待文件或手册核实。 [官方入口](https://www.fao.org/geospatial/data-and-tools/tools/land-cover-toolbox/)
- LEGAL_TOPICS: 公开再分发许可待核实；官方映射及精确端点版本待核实；明确版本待核实；原始层级待文件或手册核实；具体发布者待确定。 [官方入口](https://www.loc.gov/catdir/cpso/lcco/)
- GETTY_AAT: 官方映射及精确端点版本待核实。 [官方入口](https://www.getty.edu/research-conservation/tools-databases/vocabularies/data-services/)
- ISCED: 公开再分发许可待核实；官方映射及精确端点版本待核实。 [官方入口](https://www.uis.unesco.org/en/methods-and-tools/isced)
- SNA_SECTORS: 公开再分发许可待核实；官方映射及精确端点版本待核实；原始层级待文件或手册核实。 [官方入口](https://unstats.un.org/unsd/econstats/national-accounts/sna2025)
- ICNPO: 公开再分发许可待核实；官方映射及精确端点版本待核实。 [官方入口](https://unstats.un.org/unsd/classifications/Family/Detail/2008)
- ICATUS: 官方映射及精确端点版本待核实；再分发适用条款待逐文件确认。 [官方入口](https://unstats.un.org/unsd/classifications/econ/)
- BEC: 原始层级待文件或手册核实；再分发适用条款待逐文件确认。 [官方入口](https://unstats.un.org/unsd/classifications/Family/Detail/1068)
- SITC: 官方映射及精确端点版本待核实；再分发适用条款待逐文件确认。 [官方入口](https://unstats.un.org/unsd/classifications/econ/)
- SIEC: 公开再分发许可待核实；官方映射及精确端点版本待核实。 [官方入口](https://unstats.un.org/unsd/Classifications/siec/)
- CEP: 公开再分发许可待核实；官方映射及精确端点版本待核实；原始层级待文件或手册核实。 [官方入口](https://seea.un.org/en/content/classification-environmental-purposes-cep)
- ICCS: 公开再分发许可待核实；官方映射及精确端点版本待核实。 [官方入口](https://unstats.un.org/unsd/classifications/Family/Detail/1000)
- EUROVOC: 公开再分发许可待核实；官方映射及精确端点版本待核实。 [官方入口](https://data.europa.eu/data/datasets/eurovoc)
- ISCED_T: 公开再分发许可待核实；官方映射及精确端点版本待核实；原始层级待文件或手册核实。 [官方入口](https://www.uis.unesco.org/en/methods-and-tools/isced)
- ICNP_TSO: 公开再分发许可待核实；官方映射及精确端点版本待核实；原始层级待文件或手册核实。 [官方入口](https://digitallibrary.un.org/record/3899725?ln=en)
- NICE: 公开再分发许可待核实；官方映射及精确端点版本待核实。 [官方入口](https://www.wipo.int/en/web/classification-nice/index)
- LOCARNO: 公开再分发许可待核实；官方映射及精确端点版本待核实。 [官方入口](https://www.wipo.int/en/web/classification-locarno)
- EBOPS: 公开再分发许可待核实；官方映射及精确端点版本待核实；原始层级待文件或手册核实。 [官方入口](https://unstats.un.org/unsd/classifications/Family/Detail/2102)
- ICSE: 公开再分发许可待核实；官方映射及精确端点版本待核实。 [官方入口](https://webapps.ilo.org/ilostat-files/Documents/ICSE-18_manual.pdf)
