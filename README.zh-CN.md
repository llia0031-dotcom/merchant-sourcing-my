# 马来西亚电子类目招商样本

马来西亚线上消费电子的招商打法：先招哪些商家、凭什么，他们的产品要哪些认证，头 30 天怎么带。每条事实都链接到公开页面，并和存档原文核对过。

[English](README.md) · [先联系谁](pool/PRIORITY.md) · [深挖：充电器和充电宝](insight/DEEP_DIVE_CHARGING.zh-CN.md) · [资质清单](onboarding/CHECKLIST.md) · [进了类目团队以后](pool/INSIDE_THE_TEAM.md)

## 发现了什么

**先联系谁**

| 排名 | 商家 | 理由（每条都有公开出处） |
|---|---|---|
| 1 | Khind，马来西亚本地家电品牌 | 年报显示 2025 年电商占营收 4.2%，直营销售从 RM27.2 million 增到 RM49.3 million；已在内容电商上但还不大；产品已获能源委员会和 SIRIM 认证 <!-- c:S05 --> |
| 2 | VSTECS，马来西亚 ICT 经销商 | 替品牌方运营官方网店，渠道伙伴超过 4,000 家；引进品牌时检查 SIRIM、MCMC 认证；没找到内容电商店 <!-- c:S06 --> |
| 3、4 | CompAsia 和 Machines，马来西亚连锁门店 | 分别约 70 家和 50 多家门店；已在运营马来西亚的短视频账号；没找到内容电商店 <!-- c:S07 --> |

完整名单、每家的下一步和公开联系渠道见 [pool/PRIORITY.md](pool/PRIORITY.md)。“没找到内容电商店”只表示在读过的公开页面里没找到；第一次联系前先查平台自己的卖家名单。

**为什么先找本地商家**

- 购物者已经在那里：Ipsos 调查显示，2026 年 62% 的马来西亚网购者用过 TikTok Shop，2025 年是 52%，2024 年是 43%。 <!-- c:S08 -->
- 那里按件数领先的电子类卖家是配件卖家，比如 FindNiche 按销量排的 100 家店里 Baseus Malaysia 第 14、UgreenOfficialShop 第 15，所以在别处卖较高价电子产品的品牌是更缺的供给。 <!-- c:S09 -->
- 本地卖家有政策顺风：500 令吉及以下进口商品的 10% 销售税 2025 年收了 RM817 juta（百万），2024 年是 RM476 juta。 <!-- c:S10 -->

**深挖一个细分品类：充电器和充电宝。** 按件数领先的商品价格在 RM0.19 到 RM16.29 之间，品牌充电器从 MYR 69 起；能源委员会的批准由马来西亚进口商持有，所以第一个电话打给品牌的本地经销商。[深挖页](insight/DEEP_DIVE_CHARGING.zh-CN.md)。 <!-- c:S13 -->

## 谁拿什么做什么

| 部分 | 谁用、用来做什么 | 文件 |
|---|---|---|
| 行业洞察和细分品类深挖 | 类目经理：先招哪些细分品类、哪类商家，用什么理由说服 | [insight/](insight/) |
| 商家池和优先级 | 招商：先打给谁、每条理由的出处、公开联系渠道、下一步 | [pool/PRIORITY.md](pool/PRIORITY.md)、[pool/merchant_pool.xlsx](pool/merchant_pool.xlsx)、[pool/queries.sql](pool/queries.sql) |
| 资质清单 | 商家（第一次通话后发过去）：要登记什么、检测什么、贴什么标签、上架页面写什么 | [onboarding/CHECKLIST.md](onboarding/CHECKLIST.md)（英文，引官方原文） |
| 入驻跟进表 | 招商：每个商家一张表，填一个首次联系日期就排出各节点，逾期和临近的自动提醒 | [onboarding/tracker_template.xlsx](onboarding/tracker_template.xlsx) |
| 头 30 天 | 带新店成长的人：每周指标、关键节点、预警 | [coldstart/](coldstart/) |
| 触达模板 | 招商：首封信、跟进、要资料、启动、第一周复盘；英文，附一段简短的马来语开场 | [outreach/TEMPLATES.md](outreach/TEMPLATES.md) |

## 进了类目团队以后

- 最弱的几格来自公开页面，也是最先换成平台自己数据的：有没有店、按商品的搜索需求、每个商品的资质记录。[pool/INSIDE_THE_TEAM.md](pool/INSIDE_THE_TEAM.md) 逐项写了换成什么、会改变什么。
- 权重是起步时的假设。第一批商家联系完以后，用 [pool/calibration.sql](pool/calibration.sql) 对比各档和各维度与“有没有入驻、第 4 周卖了多少”的关系；要改权重，就在给下一批打分之前先写死新版本。

## 怎么做的

- **先用现成的。** 店铺排行工具只排已经在平台上的商家，卖家后台的工具要卖家登录。这份样本补的是还没进来或还没做起来的商家，现成工具的公开页面当输入。
- **只读公开页面，** 一次一页，先查 robots.txt（包括网站写给 AI 助手的规则），同一网站至少隔八秒，不登录，不读电商平台的商品页、店铺页、搜索页。页面原文归原发布方：[sources/manifests/](sources/manifests/) 列出每个网址、读取时间和指纹，[tools/refetch.py](tools/refetch.py) 可以重新保存。
- **资质只引监管机构：** 能源委员会、MCMC、SIRIM QAS、KPDN、皇家关税局、SSM。资料齐全时能源委员会的新批准 5 个工作日办完，MCMC 要求在商品页写明认证情况。 <!-- c:S11 -->
- **按打分前写死的规则打分。** [pool/SCORING.md](pool/SCORING.md) 的变更记录写明 v2 在任何一行打分之前替换了 v1；规则一改，[pool/build.py](pool/build.py) 就拒绝打分。 <!-- c:S12 -->
- **每条事实都核对过**，用 [evidence-check](https://github.com/llia0031-dotcom/evidence-check) 对回存档原文：商家池由 [pool/build.py](pool/build.py) 核对，文档由 [tools/check_all.py](tools/check_all.py) 核对。

规模：存了 183 个公开页面，其中 131 个被引用；商家池 42 家（品牌 33、经销商 1、连锁店 8），覆盖 9 个细分品类，23 家有马来西亚公司或具名的马来西亚经销商；商家池里 303 个格子，每个都有在存档页面里找得到的原文；A 档 14 家、B 档 20 家、C 档 8 家；17 家帮它开第一家内容电商店，18 家帮已开的店做起来。 <!-- c:S14 -->

## 怎么运行

需要 Python 3.10 以上，命令见 [英文版](README.md#run-it)。

## 局限

- “公开来源里没找到”不是对任何商家的评价，也不表示店铺或认证不存在。
- 研究机构和数据工具给的销量数字是它们的估算；店铺榜只来自一个数据集，按件数排序。
- 家电和手机电子放在一起，因为本地家电品牌是最强的本地候选之一。
- 没有联系过任何商家，触达模板没有发出过。
- `coldstart/example/` 里的数据是虚构的，只用来测试 SQL。

## 和其他项目的关系

属于同一组项目，主线是“每一句话都拿出证据”。[evidence-check](https://github.com/llia0031-dotcom/evidence-check) 是这里用的核对工具；头 30 天的 SQL 沿用 [Grounded Business Review](https://github.com/llia0031-dotcom/grounded-business-review) 的周指标做法。

代码 MIT。事实和短引文来自清单里写明的发布方。这是基于公开来源的独立研究，与文中提到的任何平台、品牌或商店没有关联。
