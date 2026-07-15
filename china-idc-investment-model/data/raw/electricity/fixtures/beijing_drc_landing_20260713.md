# 北京市发展和改革委员会 - 首页 fixture
# 抓取日期: 2026-07-13
# 源 URL: https://fgw.beijing.gov.cn/
# 用途: 演示从省级发改委首页提取政策文件链接的解析流程

## meta
- SiteDomain: fgw.beijing.gov.cn
- SiteName: 北京市发展和改革委员会
- SiteIDCode: 1100000011

## 关键政策/公示链接（首页可见）
- 政策文件目录: https://fgw.beijing.gov.cn/fgwzwgk/2024zcwj/
- 政策解读: https://fgw.beijing.gov.cn/fgwzwgk/2024zcjd/
- 政府信息公开: https://fgw.beijing.gov.cn/fgwzwgk/zfxxgk/
- 行政许可公示: https://fgw.beijing.gov.cn/fzggzl/yfxz/xzxk_sgs/
- 便民数据: https://fgw.beijing.gov.cn/bmcx/djcx/sp/

## 首页近期公告示例
- 2026-07-09: 北京市发展和改革委员会关于公示地热能高质量开发利用试点评审结果的通知
- 2026-07-03: 本市成品油价格调整
- 2026-06-23: 北京医院通过清洁生产绩效验收的通知
- 2026-07-08: 关于燕落寨110千伏输变电工程核准的批复
- 2026-07-07: 关于集成电路产业园建设项目的节能审查意见

## 从首页可以提取的价格/能源相关话题（关键词命中）
- 电价：0 处（首页不显示，需进入政策文件目录）
- 输变电工程：3 处（表明电网侧信息公开活跃）
- 节能审查：1 处（表明 IDC 项目节能审查是常规流程）
- 成品油价格：1 处（价格公告有规律发布）

## 结论
北京市发改委首页不直接列示工商业电价，需进入 fgwzwgk/2024zcwj/ 二级页面，
再按关键词"工商业目录电价"或"输配电价"过滤才能找到具体 PDF/HTML。
生产环境的推荐流程：定时抓取政策文件目录 → 关键词匹配 → 下载对应 PDF → 用 pdfplumber 或 LLM 提取。
