"""气候数据采集

数据中心 PUE 与年均气温强相关：
- 年均 < 10°C：可大量自然冷却，PUE 可做到 1.15-1.2
- 10-15°C：PUE 1.2-1.3
- > 20°C：PUE 1.4+

数据源：
- 本地参考表：data/reference/city_climate.csv（30 年气候常态值，开箱即用）
- API 可选：Open-Meteo（免费，无需 key）
"""
from __future__ import annotations
from pathlib import Path
import pandas as pd
import requests


REF_FILE = Path(__file__).parent.parent.parent / 'data' / 'reference' / 'city_climate.csv'


def load_reference_climate() -> pd.DataFrame:
    """加载本地参考气候数据"""
    return pd.read_csv(REF_FILE)


def fetch_open_meteo_historical(latitude: float, longitude: float,
                                 start_date: str = '2020-01-01',
                                 end_date: str = '2024-12-31') -> pd.DataFrame:
    """
    从 Open-Meteo 拉取历史日均温度（免费API）

    Parameters
    ----------
    latitude, longitude : 经纬度
    start_date, end_date : YYYY-MM-DD

    Returns
    -------
    DataFrame 列：date, temp_mean_c, temp_max_c, temp_min_c
    """
    url = "https://archive-api.open-meteo.com/v1/archive"
    params = {
        'latitude': latitude,
        'longitude': longitude,
        'start_date': start_date,
        'end_date': end_date,
        'daily': 'temperature_2m_mean,temperature_2m_max,temperature_2m_min',
        'timezone': 'Asia/Shanghai',
    }
    try:
        r = requests.get(url, params=params, timeout=30)
        r.raise_for_status()
        data = r.json()['daily']
        return pd.DataFrame({
            'date': pd.to_datetime(data['time']),
            'temp_mean_c': data['temperature_2m_mean'],
            'temp_max_c': data['temperature_2m_max'],
            'temp_min_c': data['temperature_2m_min'],
        })
    except Exception as e:
        print(f"Open-Meteo API 失败: {e}")
        return pd.DataFrame()


def estimate_pue_from_climate(avg_annual_temp_c: float) -> float:
    """
    根据年均温度粗略估算最佳 PUE

    经验公式（基于行业实证）：
    - 6°C  → PUE 1.15
    - 10°C → PUE 1.20
    - 15°C → PUE 1.25
    - 20°C → PUE 1.32
    - 25°C → PUE 1.40
    """
    if avg_annual_temp_c <= 6:
        return 1.15
    elif avg_annual_temp_c <= 10:
        return 1.20
    elif avg_annual_temp_c <= 15:
        return 1.25
    elif avg_annual_temp_c <= 20:
        return 1.32
    else:
        return 1.40


def enrich_cities_with_pue(cities_df: pd.DataFrame,
                           climate_df: pd.DataFrame = None) -> pd.DataFrame:
    """给候选城市加上估算的最佳 PUE"""
    climate_df = climate_df if climate_df is not None else load_reference_climate()
    temp_map = dict(zip(climate_df['city'], climate_df['avg_annual_temp_c']))
    df = cities_df.copy()
    df['avg_temp_c'] = df['city'].map(temp_map).fillna(15)
    df['estimated_pue'] = df['avg_temp_c'].apply(estimate_pue_from_climate)
    return df


if __name__ == '__main__':
    climate = load_reference_climate()
    print("=== 城市气候 → 估算最佳 PUE ===\n")
    climate['estimated_pue'] = climate['avg_annual_temp_c'].apply(estimate_pue_from_climate)
    cols = ['city', 'avg_annual_temp_c', 'cooling_advantage_score', 'estimated_pue']
    sorted_df = climate.sort_values('estimated_pue')
    print(sorted_df[cols].head(15).to_string(index=False))
