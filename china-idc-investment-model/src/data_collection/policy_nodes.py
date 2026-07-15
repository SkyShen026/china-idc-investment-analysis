"""东数西算政策节点数据加载

8 大枢纽节点 + 10 个集群是 2022 年国家发改委等四部委确定的固定布局。
这里直接加载手工整理的参考数据，并提供查询接口。

来源：《全国一体化大数据中心协同创新体系算力枢纽实施方案》
"""
from __future__ import annotations
from pathlib import Path
import pandas as pd


REF_FILE = Path(__file__).parent.parent.parent / 'data' / 'reference' / 'dongshuxisuan_nodes.csv'


def load_nodes() -> pd.DataFrame:
    """加载所有东数西算节点"""
    return pd.read_csv(REF_FILE)


def get_hubs() -> pd.DataFrame:
    """8 大枢纽节点"""
    df = load_nodes()
    return df[df['node_type'] == 'hub']


def get_clusters() -> pd.DataFrame:
    """10 个集群"""
    df = load_nodes()
    return df[df['node_type'] == 'cluster']


def get_node_score(city: str) -> int:
    """查询某城市的政策节点分（节点20 / 集群10 / 其他0）"""
    df = load_nodes()
    matched = df[df['key_city'].str.contains(city, na=False)]
    if matched.empty:
        return 0
    return int(matched['policy_score'].max())


def is_eastern_hub(city: str) -> bool:
    """是否东部枢纽（京津冀/长三角/粤港澳/成渝）"""
    eastern_hubs = ['张家口', '上海', '苏州', '嘉兴', '韶关', '天府', '重庆', '青浦']
    return any(h in city for h in eastern_hubs)


def is_western_hub(city: str) -> bool:
    """是否西部枢纽（内蒙古/贵州/甘肃/宁夏）"""
    western_hubs = ['和林格尔', '贵安新区', '庆阳', '中卫']
    return any(h in city for h in western_hubs)


if __name__ == '__main__':
    print("=== 8 大枢纽节点 ===")
    print(get_hubs()[['name', 'province', 'key_city']].to_string(index=False))
    print("\n=== 10 个集群 ===")
    print(get_clusters()[['name', 'province', 'key_city']].to_string(index=False))
    print(f"\n贵安新区政策分: {get_node_score('贵安新区')}")
    print(f"贵阳政策分: {get_node_score('贵阳')}")
