"""项目 IRR / NPV / Cap Rate 计算"""
from __future__ import annotations
import numpy as np
import numpy_financial as npf
import pandas as pd

from .revenue import RevenueAssumption, revenue_stream, TYPICAL_RAMP_CURVE
from .cost import CostAssumption, total_capex, opex_stream


TAX_RATE = 0.25  # 企业所得税 25%


def build_cashflow(rev_assumption: RevenueAssumption,
                   cost_assumption: CostAssumption,
                   tax_rate: float = TAX_RATE) -> pd.DataFrame:
    """
    构建项目现金流表

    约定：
    - Year 0: CAPEX 全部投入（简化，实际可拆 1-2 年）
    - Year 1-N: 经营现金流
    - 终值：第 N 年加入残值（按账面净值的 30%）
    """
    years = list(range(0, len(rev_assumption.occupancy_ramp) + 1))
    revenue = [0] + revenue_stream(rev_assumption)
    opex_list = [{'total': 0, 'cash_opex': 0, 'depreciation': 0}] + \
                opex_stream(cost_assumption, rev_assumption.occupancy_ramp)

    capex = total_capex(cost_assumption)
    rev_arr = np.array(revenue)
    ebitda = rev_arr - np.array([o['cash_opex'] for o in opex_list])
    depreciation = np.array([o['depreciation'] for o in opex_list])
    ebit = ebitda - depreciation
    tax = np.where(ebit > 0, ebit * tax_rate, 0)
    net_income = ebit - tax
    operating_cf = net_income + depreciation  # 加回折旧

    # CAPEX 在 Year 0
    investment = np.zeros(len(years))
    investment[0] = -capex

    # 终值：第 N 年加入残值
    terminal_value = capex - depreciation.sum()  # 账面净值
    terminal_value = max(terminal_value * 0.3, 0)  # 残值率 30%
    fcf = operating_cf + investment
    fcf[-1] += terminal_value

    df = pd.DataFrame({
        'year': years,
        'revenue': revenue,
        'cash_opex': [o['cash_opex'] for o in opex_list],
        'ebitda': ebitda,
        'depreciation': depreciation,
        'ebit': ebit,
        'tax': tax,
        'net_income': net_income,
        'operating_cf': operating_cf,
        'investment': investment,
        'fcf': fcf,
    })
    df.attrs['terminal_value'] = terminal_value
    df.attrs['capex'] = capex
    return df


def calculate_irr(fcf: list[float] | np.ndarray) -> float:
    """计算 IRR"""
    irr = npf.irr(list(fcf))
    return float(irr) if irr is not None and not np.isnan(irr) else np.nan


def calculate_npv(fcf: list[float] | np.ndarray, discount_rate: float) -> float:
    """计算 NPV"""
    return float(npf.npv(discount_rate, list(fcf)))


def calculate_cap_rate(annual_noi: float, asset_value: float) -> float:
    """Cap Rate = NOI / 资产价值"""
    return annual_noi / asset_value if asset_value > 0 else 0


def calculate_idc_irr(city: str,
                      rack_count: int = 1000,
                      rack_power_kw: float = 8.0,
                      pue: float = 1.25,
                      electricity_price: float = 0.40,
                      rack_monthly_revenue: float = 4500,
                      capex_per_rack: float = 80000,
                      ramp_curve: str = 'standard',
                      project_years: int = 10,
                      discount_rate: float = 0.08) -> dict:
    """
    端到端：给定一个城市的参数，输出 IRR / NPV / Cap Rate

    Returns
    -------
    dict {city, irr, npv, cap_rate_stabilized, payback_years, cashflow_df}
    """
    ramp = TYPICAL_RAMP_CURVE[ramp_curve][:project_years]

    rev_a = RevenueAssumption(
        rack_count=rack_count,
        monthly_rent_per_rack=rack_monthly_revenue,
        occupancy_ramp=ramp,
    )
    cost_a = CostAssumption(
        rack_count=rack_count,
        rack_power_kw=rack_power_kw,
        pue=pue,
        electricity_price=electricity_price,
        capex_per_rack=capex_per_rack,
    )

    cf = build_cashflow(rev_a, cost_a)
    fcf = cf['fcf'].values

    irr = calculate_irr(fcf)
    npv = calculate_npv(fcf, discount_rate)

    # 稳定期 Cap Rate：用第 4 年的 NOI / 总投资
    stable_noi = cf.iloc[4]['ebitda']  # EBITDA 近似 NOI
    cap_rate = calculate_cap_rate(stable_noi, cf.attrs['capex'])

    # 回收期（cumulative FCF turns positive）
    cum_fcf = np.cumsum(fcf)
    payback = next((i for i, v in enumerate(cum_fcf) if v > 0), None)

    return {
        'city': city,
        'irr': irr,
        'npv': npv,
        'cap_rate_stabilized': cap_rate,
        'payback_years': payback,
        'total_capex': cf.attrs['capex'],
        'cashflow_df': cf,
    }


if __name__ == '__main__':
    result = calculate_idc_irr(
        city='贵阳',
        rack_count=1000,
        rack_power_kw=8,
        pue=1.25,
        electricity_price=0.35,
        rack_monthly_revenue=3500,
        capex_per_rack=80000,
    )
    print(f"\n=== {result['city']} ===")
    print(f"IRR: {result['irr']:.2%}")
    print(f"NPV @ 8%: ¥{result['npv']/1e6:.1f}M")
    print(f"Cap Rate (stabilized): {result['cap_rate_stabilized']:.2%}")
    print(f"Payback: {result['payback_years']} years")
    print(f"\nCash Flow (¥M):")
    cf_display = result['cashflow_df'].copy()
    for col in ['revenue', 'cash_opex', 'ebitda', 'net_income', 'fcf']:
        cf_display[col] = (cf_display[col] / 1e6).round(2)
    print(cf_display[['year', 'revenue', 'cash_opex', 'ebitda', 'net_income', 'fcf']].to_string(index=False))
