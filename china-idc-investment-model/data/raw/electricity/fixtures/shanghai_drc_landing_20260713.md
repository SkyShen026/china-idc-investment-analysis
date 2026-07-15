# 上海市发展和改革委员会 - 首页 fixture
# 抓取日期: 2026-07-13
# 源 URL: https://fgw.sh.gov.cn/
# 用途: 演示上海市发改委价格公告的抓取流程

## meta
- SiteDomain: fgw.sh.gov.cn
- SiteName: 上海市发展和改革委员会
- SiteIDCode: 3100000087

## 关键价格相关链接
- 价格管理专栏（价格公告主要来源）: https://fgw.sh.gov.cn/fgw_jggl/
- 政策文件: https://fgw.sh.gov.cn/fgw_zcwjfl/
- 政策解读: https://fgw.sh.gov.cn/fgw_zcjd/

## 首页近期价格公告示例
- 2026-05-21: 上海市发展和改革委员会关于车用汽、柴油价格的通知（2026年5月21日）
  URL: https://fgw.sh.gov.cn/fgw_jggl/20260521/666d56f01c244cd281a3d11170710d12.html
- 2026-05-21: 5月中旬，我市主副食品价格稳中回落
- 2026-05-19: 关于我市宗教场所和监狱监房生活用水、用电、用气执行居民价格的通知
  URL: https://fgw.sh.gov.cn/fgw_jggl/20260519/d46b2ca9d43f45baac66c22f547b1553.html

## 结论
上海市发改委价格公告位于 fgw_jggl/ 子路径，URL 模式为
  /fgw_jggl/YYYYMMDD/<hash>.html
可以每日抓取该子路径列表页，按日期过滤新增公告。
工商业电价通常通过"关于调整本市工商业电价的通知"等标题发布，
可用标题关键词过滤 + LLM 或正则提取具体价格数字。
