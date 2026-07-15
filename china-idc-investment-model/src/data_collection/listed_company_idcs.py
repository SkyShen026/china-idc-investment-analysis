"""上市公司 IDC 数据采集

通过 akshare（开源金融数据库）拉取 IDC 上市公司财务数据。
配合手工整理的 listed_idc_companies.csv 使用。
"""
from __future__ import annotations
from pathlib import Path
import pandas as pd


REF_FILE = Path(__file__).parent.parent.parent / 'data' / 'reference' / 'listed_idc_companies.csv'


def load_companies() -> pd.DataFrame:
    """加载 IDC 上市公司清单"""
    return pd.read_csv(REF_FILE)


def fetch_financial_data_akshare(ticker: str, exchange: str = 'SZSE') -> pd.DataFrame:
    """
    用 akshare 抓取财务数据（A 股可用）

    使用前：pip install akshare
    """
    try:
        import akshare as ak
    except ImportError:
        print("pip install akshare 后才能调用")
        return pd.DataFrame()

    try:
        if exchange in ('SZSE', 'SSE'):
            # A 股
            df = ak.stock_financial_abstract(symbol=ticker)
            return df
        else:
            print(f"美股 ticker {ticker} 请使用 yfinance")
            return pd.DataFrame()
    except Exception as e:
        print(f"获取失败 {ticker}: {e}")
        return pd.DataFrame()


def fetch_us_listed_via_yfinance(ticker: str) -> dict:
    """
    抓取美股 IDC 公司基本数据（GDS, VNET）

    使用前：pip install yfinance
    """
    try:
        import yfinance as yf
    except ImportError:
        print("pip install yfinance 后才能调用")
        return {}

    try:
        t = yf.Ticker(ticker)
        info = t.info
        return {
            'ticker': ticker,
            'name': info.get('longName'),
            'market_cap_usd': info.get('marketCap'),
            'revenue_ttm_usd': info.get('totalRevenue'),
            'enterprise_value': info.get('enterpriseValue'),
            'pe_ratio': info.get('trailingPE'),
            'ps_ratio': info.get('priceToSalesTrailing12Months'),
        }
    except Exception as e:
        print(f"获取失败 {ticker}: {e}")
        return {}


def get_market_overview() -> pd.DataFrame:
    """快速获取 IDC 行业市值/收入概览"""
    df = load_companies()
    df['market_cap_usd_eq'] = df['market_cap_cny_bn'] * 0.14  # 粗略汇率
    df['ev_per_rack'] = (df['market_cap_cny_bn'] * 1e9 / df['total_racks_2024']).round(0)
    return df[['company', 'ticker', 'exchange', 'total_racks_2024',
               'fy2024_revenue_cny_bn', 'market_cap_cny_bn', 'ev_per_rack']]


if __name__ == '__main__':
    print("=== IDC 行业上市公司概览 ===\n")
    df = get_market_overview()
    print(df.to_string(index=False))

    print("\n=== 单机柜估值（市值/机柜数）行业基准 ===")
    df_filtered = df[df['total_racks_2024'].notna()]
    print(f"平均单机柜估值: ¥{df_filtered['ev_per_rack'].mean():,.0f}")
    print(f"中位数: ¥{df_filtered['ev_per_rack'].median():,.0f}")
