"""成本模型：数据中心 OPEX/CAPEX

电力成本占 OPEX 55-70%，是核心变量。
"""
from dataclasses import dataclass


HOURS_PER_YEAR = 8760


@dataclass
class CostAssumption:
    rack_count: int
    rack_power_kw: float = 6.0          # 单机柜 IT 功率，AI 训练可到 30
    pue: float = 1.25                    # 电源使用效率
    electricity_price: float = 0.40      # 元/kWh（数据中心专项电价）
    capex_per_rack: float = 80000        # 单机柜建设成本（建筑+机电）
    depreciation_years: int = 10         # 折旧年限（机电主流）
    staff_cost_per_rack_year: float = 1500  # 人力分摊
    maintenance_pct: float = 0.03        # 维护费占 CAPEX 比例
    other_opex_per_rack_year: float = 800   # 网络+耗材+税费


def total_capex(assumption: CostAssumption) -> float:
    """总 CAPEX（一次性投入）"""
    return assumption.rack_count * assumption.capex_per_rack


def annual_electricity_cost(assumption: CostAssumption, occupancy: float = 1.0) -> float:
    """
    年度电费

    电费 = 单机柜功率 × 机柜数 × PUE × 8760h × 电价 × 入住率
    """
    it_load_kw = assumption.rack_count * assumption.rack_power_kw * occupancy
    total_kwh = it_load_kw * assumption.pue * HOURS_PER_YEAR
    return total_kwh * assumption.electricity_price


def annual_opex(assumption: CostAssumption, occupancy: float = 1.0) -> dict:
    """
    年度 OPEX 拆分

    Returns
    -------
    dict 各项成本（元）
    """
    capex = total_capex(assumption)
    electricity = annual_electricity_cost(assumption, occupancy)
    depreciation = capex / assumption.depreciation_years
    staff = assumption.rack_count * assumption.staff_cost_per_rack_year
    maintenance = capex * assumption.maintenance_pct
    other = assumption.rack_count * assumption.other_opex_per_rack_year

    return {
        'electricity': electricity,
        'depreciation': depreciation,
        'staff': staff,
        'maintenance': maintenance,
        'other': other,
        'total': electricity + depreciation + staff + maintenance + other,
        'cash_opex': electricity + staff + maintenance + other,  # 不含折旧的现金成本
    }


def opex_stream(assumption: CostAssumption, occupancy_ramp: tuple) -> list[dict]:
    """多年 OPEX 流（按入住率调整电费/其他变动成本）"""
    out = []
    for occ in occupancy_ramp:
        out.append(annual_opex(assumption, occupancy=occ))
    return out


if __name__ == '__main__':
    assumption = CostAssumption(
        rack_count=1000,
        rack_power_kw=8,
        pue=1.25,
        electricity_price=0.35,   # 贵阳数据中心专项价
        capex_per_rack=80000,
    )
    capex = total_capex(assumption)
    opex_full = annual_opex(assumption, occupancy=0.90)
    print(f"Total CAPEX: ¥{capex/1e6:.1f}M")
    print(f"Annual OPEX (90% occupancy):")
    for k, v in opex_full.items():
        print(f"  {k:15s}: ¥{v/1e6:>7.2f}M")
