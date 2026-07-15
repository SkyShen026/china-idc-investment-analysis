"""综合选址评分模型

把多个维度（电价、政策、气候、距离需求、电网容量等）归一化打分，
按权重加权得到 0-100 的综合评分。
"""
from __future__ import annotations
import pandas as pd
import numpy as np
from pathlib import Path


DEFAULT_WEIGHTS = {
    'electricity_price': 0.30,    # 电价（越低越好）
    'policy_node': 0.20,          # 东数西算节点（越高越好）
    'cooling_climate': 0.15,      # 散热气候（越冷越好）
    'demand_proximity': 0.15,     # 距需求中心（越近越好）
    'grid_capacity': 0.10,        # 电网容量（越大越好）
    'land_cost': 0.05,            # 土地成本（越低越好）
    'gov_subsidy': 0.05,          # 政府补贴（越高越好）
}


def _normalize_lower_better(series: pd.Series) -> pd.Series:
    """越低越好 → 归一化到 0-100"""
    min_v, max_v = series.min(), series.max()
    if max_v == min_v:
        return pd.Series([50] * len(series), index=series.index)
    return (1 - (series - min_v) / (max_v - min_v)) * 100


def _normalize_higher_better(series: pd.Series) -> pd.Series:
    """越高越好 → 归一化到 0-100"""
    min_v, max_v = series.min(), series.max()
    if max_v == min_v:
        return pd.Series([50] * len(series), index=series.index)
    return (series - min_v) / (max_v - min_v) * 100


def score_cities(cities_df: pd.DataFrame,
                 power_df: pd.DataFrame,
                 climate_df: pd.DataFrame,
                 nodes_df: pd.DataFrame,
                 weights: dict = None) -> pd.DataFrame:
    """
    对候选城市综合打分

    Parameters
    ----------
    cities_df : 候选城市基础信息（candidate_cities.csv）
    power_df : 各省电价（provincial_power_price.csv）
    climate_df : 城市气候（city_climate.csv）
    nodes_df : 东数西算节点（dongshuxisuan_nodes.csv）
    weights : 维度权重

    Returns
    -------
    DataFrame 含各维度分数 + 综合分
    """
    weights = weights or DEFAULT_WEIGHTS
    df = cities_df.copy()

    # 1. 电价（用省份匹配 data_center_special_price）
    power_map = dict(zip(power_df['province'], power_df['data_center_special_price']))
    df['power_price'] = df['province'].map(power_map).fillna(df['province'].map(
        dict(zip(power_df['province'], power_df['industrial_price_yuan_per_kwh']))))

    # 2. 政策节点分（policy_score = 节点 20，集群 10，其他 0）
    node_score_map = {}
    for _, row in nodes_df.iterrows():
        city = row['key_city'].split('/')[0]
        node_score_map[city] = max(node_score_map.get(city, 0), row['policy_score'])
    df['policy_score'] = df['city'].map(node_score_map).fillna(0)

    # 3. 气候散热分
    climate_map = dict(zip(climate_df['city'], climate_df['cooling_advantage_score']))
    df['cooling_score'] = df['city'].map(climate_map).fillna(5)

    # 4. 距需求中心（直接用候选城市表里的 distance_to_demand_km，但需要反转）
    df['demand_proximity_raw'] = df['distance_to_demand_km']  # 越小越好

    # 归一化各维度
    df['s_electricity'] = _normalize_lower_better(df['power_price'])
    df['s_policy'] = _normalize_higher_better(df['policy_score'])
    df['s_climate'] = _normalize_higher_better(df['cooling_score'])
    df['s_demand'] = _normalize_lower_better(df['demand_proximity_raw'])
    df['s_grid'] = _normalize_higher_better(df['grid_capacity_score'])
    df['s_land'] = _normalize_lower_better(df['land_cost_per_sqm'])
    df['s_subsidy'] = _normalize_higher_better(df['gov_subsidy_score'])

    # 加权综合分
    df['composite_score'] = (
        df['s_electricity'] * weights['electricity_price'] +
        df['s_policy'] * weights['policy_node'] +
        df['s_climate'] * weights['cooling_climate'] +
        df['s_demand'] * weights['demand_proximity'] +
        df['s_grid'] * weights['grid_capacity'] +
        df['s_land'] * weights['land_cost'] +
        df['s_subsidy'] * weights['gov_subsidy']
    )

    return df.sort_values('composite_score', ascending=False).reset_index(drop=True)


def load_all_data(ref_dir: str | Path = None) -> dict:
    """一次性加载所有参考数据"""
    if ref_dir is None:
        # 默认相对于本文件
        ref_dir = Path(__file__).parent.parent.parent / 'data' / 'reference'
    ref_dir = Path(ref_dir)
    return {
        'cities': pd.read_csv(ref_dir / 'candidate_cities.csv'),
        'power': pd.read_csv(ref_dir / 'provincial_power_price.csv'),
        'climate': pd.read_csv(ref_dir / 'city_climate.csv'),
        'nodes': pd.read_csv(ref_dir / 'dongshuxisuan_nodes.csv'),
        'companies': pd.read_csv(ref_dir / 'listed_idc_companies.csv'),
    }


if __name__ == '__main__':
    data = load_all_data()
    scored = score_cities(data['cities'], data['power'], data['climate'], data['nodes'])
    print("\n=== Top 10 选址城市（综合评分）===\n")
    cols = ['city', 'province', 'tier', 'power_price', 'policy_score',
            'cooling_score', 'composite_score']
    print(scored[cols].head(10).to_string(index=False))
