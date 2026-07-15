# China IDC Investment Model | 中国数据中心投资量化模型

> 一个面向 AI 算力基建投资分析的量化决策工具：输入候选城市 → 输出 IRR、Cap Rate、综合选址评分 → 可视化全国机会热力图。

**作者**：Sky Shen（经济学 + 房地产/基础设施 + Data Science，CFA L1 在考）
**用途**：金融求职作品集 · 算力基建投资分析 · "东数西算"政策落地量化研究

---

## 项目亮点

- **三段背景闭环**：实物资产（IDC 是地产+基建）+ 财务建模（IRR/Cap Rate）+ 数据科学（量化打分 + 可视化）
- **回答一个真实的投资问题**：在 25 个候选城市中，哪 5 个是未来 5 年新建 AI 数据中心的最佳标的？
- **完整 pipeline**：数据采集 → 清洗 → 财务建模 → 评分 → 可视化 → 投资建议

## 项目结构

```
china-idc-investment-model/
├── docs/
│   └── 技术方案.md              ← 设计文档（先读这个）
├── data/
│   ├── reference/               ← 手工整理的基准数据（开箱即用）
│   │   ├── dongshuxisuan_nodes.csv     东数西算 8+10 节点
│   │   ├── provincial_power_price.csv  各省工商业电价基准
│   │   ├── city_climate.csv            主要城市气候 / 平均温度
│   │   ├── listed_idc_companies.csv    A股+美股 IDC 上市公司
│   │   └── candidate_cities.csv        25 个候选选址城市
│   ├── raw/                     原始下载数据（脚本写入）
│   └── processed/               清洗后数据
├── src/
│   ├── data_collection/         数据采集模块
│   │   ├── electricity_prices.py
│   │   ├── policy_nodes.py
│   │   ├── listed_company_idcs.py
│   │   └── climate_data.py
│   ├── model/                   财务模型
│   │   ├── revenue.py           收入模型（机柜租赁）
│   │   ├── cost.py              成本模型（电力为大头）
│   │   ├── irr.py               IRR / NPV 计算
│   │   └── site_score.py        综合选址评分
│   └── visualization/           可视化
│       ├── china_map.py         全国选址热力图
│       └── charts.py            敏感性分析图表
├── notebooks/
│   └── 01_demo_end_to_end.ipynb 端到端演示（面试用）
├── requirements.txt
└── .gitignore
```

## 快速开始

```bash
# 1. 克隆 + 安装
git clone <your-repo-url>
cd china-idc-investment-model
pip install -r requirements.txt

# 2. 运行端到端 demo
jupyter notebook notebooks/01_demo_end_to_end.ipynb

# 3. 单独运行模型
python -c "
from src.model.irr import calculate_idc_irr
result = calculate_idc_irr(
    city='贵阳',
    rack_count=1000,
    pue=1.25,
    electricity_price=0.35,
    rack_monthly_revenue=4500,
    capex_per_rack=80000,
    project_years=10,
    discount_rate=0.08
)
print(f'IRR: {result[\"irr\"]:.2%} | NPV: ¥{result[\"npv\"]/1e6:.1f}M')
"
```

## 核心结论示例（demo 输出）

| Rank | 城市 | 综合评分 | 预测 IRR | 主要优势 |
|---|---|---|---|---|
| 1 | 贵安新区 | 92 | 14.2% | 全国最低电价 + 政策节点 + 气候 |
| 2 | 中卫 | 90 | 13.8% | 西部节点 + 沙漠气候散热 |
| 3 | 张家口 | 87 | 12.5% | 京津冀延伸 + 风电富集 |
| 4 | 庆阳 | 86 | 12.1% | 西北节点 + 低成本 |
| 5 | 韶关 | 82 | 11.0% | 粤港澳延伸 + 距需求近 |

## 关键假设来源

所有硬编码数字都标注了来源（见 `data/reference/*.csv` 的备注列）：
- 电价数据：各省发改委 2024-2025 年工商业电价文件
- 东数西算节点：国家发改委等四部委 2022 年《全国一体化大数据中心协同创新体系算力枢纽实施方案》
- 上市公司数据：各公司 2024 年报、Wind
- 气候数据：中国气象局 30 年平均

## 局限性 (面试时主动讲)

1. 未考虑客户分布的延迟敏感性
2. 电价为基准价，未考虑大用户协议价格
3. 未考虑碳配额对 PUE 的隐性约束
4. 现金流模型简化，未考虑分期投入

## License

MIT (仅用于个人作品集展示)
