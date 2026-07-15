"""收入模型：数据中心机柜租赁收入"""
from dataclasses import dataclass


@dataclass
class RevenueAssumption:
    """收入假设"""
    rack_count: int                    # 机柜总数
    monthly_rent_per_rack: float       # 单机柜月租金（元）
    occupancy_ramp: tuple              # 入住率爬坡 (Y1, Y2, Y3, ..., Yn)
    annual_price_growth: float = 0.02  # 年度租金涨幅，默认 2%


def annual_revenue(rack_count: int, monthly_rent: float, occupancy: float,
                   price_growth_year: int = 0, base_growth: float = 0.02) -> float:
    """
    单年收入

    Parameters
    ----------
    rack_count : 机柜总数
    monthly_rent : 第一年单机柜月租金（元）
    occupancy : 当年入住率 (0-1)
    price_growth_year : 距第一年的年数（用于复利涨价）
    base_growth : 年度涨价率

    Returns
    -------
    年度收入（元）
    """
    price_t = monthly_rent * (1 + base_growth) ** price_growth_year
    return rack_count * price_t * 12 * occupancy


def revenue_stream(assumption: RevenueAssumption) -> list[float]:
    """生成多年收入流"""
    out = []
    for year_idx, occ in enumerate(assumption.occupancy_ramp):
        out.append(annual_revenue(
            rack_count=assumption.rack_count,
            monthly_rent=assumption.monthly_rent_per_rack,
            occupancy=occ,
            price_growth_year=year_idx,
            base_growth=assumption.annual_price_growth,
        ))
    return out


# 行业基准入住率爬坡曲线（基于上市公司年报实证）
TYPICAL_RAMP_CURVE = {
    'aggressive': (0.30, 0.65, 0.85, 0.92, 0.93, 0.93, 0.93, 0.93, 0.92, 0.90),  # 一线城市
    'standard':   (0.20, 0.50, 0.75, 0.85, 0.88, 0.88, 0.87, 0.87, 0.85, 0.83),  # 二线
    'conservative': (0.15, 0.40, 0.60, 0.75, 0.82, 0.85, 0.85, 0.83, 0.80, 0.78), # 西部
}


if __name__ == '__main__':
    # 示例：贵阳 1000 机柜
    assumption = RevenueAssumption(
        rack_count=1000,
        monthly_rent_per_rack=3500,
        occupancy_ramp=TYPICAL_RAMP_CURVE['conservative'],
    )
    stream = revenue_stream(assumption)
    for i, r in enumerate(stream, 1):
        print(f"Year {i}: ¥{r/1e6:>7.2f}M  (occupancy {assumption.occupancy_ramp[i-1]:.0%})")
