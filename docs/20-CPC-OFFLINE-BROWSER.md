# CPC 3.0 产品目录离线试点

2026-11-09 使用 Chrome `156.0.8078.80` 从来源注册表选择「产品与服务」，进入 CPC 3.0 五级源目录。实测逐级展开、按代码检索和使用稳定链接，随后从 CPC 页返回并恢复原领域筛选。CPC 以产品与服务为分类对象。ISIC 的经济活动有独立入口。 [浏览器验收脚本](../scripts/check_cpc_browser.js)

| CPC 3.0 源节点 | Chrome 实测 |
| --- | --- |
| `CPC:3.0:17400` | 逐级展开 `1 → 17 → 174 → 1740 → 17400`。结构 CSV 第 531 行。说明 PDF 物理第 63 页列天然冰雪、人工冻结水，以及指向食用冰 `22270`、干冰 `34210` 的排除条款。点击 `22270` 进入另一条产品路径。 |
| `CPC:3.0:22270` | 逐级展开 `2 → 22 → 222 → 2227 → 22270`。结构 CSV 第 781 行。说明 PDF 物理第 101 页的条目仅列标题，页面保留这一状态。可从原文排除指向的回查入口返回 `17400`。 |

Chrome 通过两处定位加载了同一锁定 PDF，分别核对 `#page=63` 和 `#page=101`。PDF 原件和实际下载的结构 CSV 均通过锁文件中的 SHA-256 核对。首次把 CSV 当文本标签页等待时，浏览器验收超时，改为显式下载后通过。 [UNSD 结构 CSV](https://unstats.un.org/unsd/classifications/Econ/Download/In%20Text/CPC_Ver_3.0_Structure_30Jun2025.csv) · [UNSD 说明 PDF](https://unstats.un.org/unsd/classifications/Econ/Download/In%20Text/CPC_Ver_3.0_Exp_Notes_30Jun2025.pdf)

锁定结构实测 4,586 个源节点、4,576 条父子边，五级节点数依次为 10、71、327、1,301、2,877。试点仅定位表中两个 PDF 条目，其中一条有说明正文。其余节点可浏览结构，说明仍待接入。稳定身份使用 CPC 版次和原码，前导零按字符串保存。PDF 排除链接保留原文方向，反查只索引这两条说明中已经收录的指向。原件与含原文的生成页保存在本地，公开报告保存定位和校验和。 [机器可读构建报告](../data/reports/cpc-offline.json) · [注册表与权利记录](../data/registry/resources.json)

验收脚本在独立临时目录中只复制锁定的两个原件及其清单，重建页面和构建报告，2/2 份产物逐字节一致。注册表的缺页、可用、过期和缺资料状态通过验证。95 项 Python 单测以及 ISIC 和家具 Chrome 离线回归通过。

已有锁定资料和 Poppler 时，在仓库根目录离线执行下列命令。Chrome 可执行文件可通过 `ATLAS_CHROME` 指定。缺资料时使用 `python3 -m atlas_sources collect --resource cpc3-structure --resource cpc3-notes-20250630` 按锁补齐。 [采集与许可说明](07-REGISTRY-AND-REPRODUCTION.md)

```sh
python3 -m atlas_sources cpc
python3 -m atlas_sources report
node scripts/check_cpc_browser.js
open data/reports/registry.html
```
