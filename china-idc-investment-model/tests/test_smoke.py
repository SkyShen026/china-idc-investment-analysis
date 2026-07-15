"""Smoke tests：跑通所有核心模块"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))


def test_load_reference_data():
    from src.model.site_score import load_all_data
    data = load_all_data()
    assert len(data['cities']) > 20
    assert len(data['power']) > 25
    assert len(data['climate']) > 20
    assert len(data['nodes']) > 15


def test_site_scoring():
    from src.model.site_score import load_all_data, score_cities
    data = load_all_data()
    scored = score_cities(data['cities'], data['power'], data['climate'], data['nodes'])
    assert 'composite_score' in scored.columns
    assert scored['composite_score'].max() <= 100
    assert scored['composite_score'].min() >= 0


def test_irr_calculation():
    from src.model.irr import calculate_idc_irr
    result = calculate_idc_irr(
        city='贵阳',
        rack_count=1000,
        electricity_price=0.35,
        rack_monthly_revenue=3500,
    )
    assert -0.5 < result['irr'] < 0.5  # IRR 在合理范围
    assert result['total_capex'] == 80_000_000  # 1000 * 80000


def test_revenue_stream():
    from src.model.revenue import revenue_stream, RevenueAssumption, TYPICAL_RAMP_CURVE
    a = RevenueAssumption(1000, 4500, TYPICAL_RAMP_CURVE['standard'])
    stream = revenue_stream(a)
    assert len(stream) == 10
    assert stream[-1] > stream[0]  # 后期收入高于前期


def test_cost_stream():
    from src.model.cost import annual_opex, CostAssumption
    a = CostAssumption(1000, electricity_price=0.40)
    o = annual_opex(a, occupancy=0.85)
    assert o['electricity'] > 0
    assert o['cash_opex'] < o['total']  # 现金成本 < 含折旧的总成本


def test_fixtures_available():
    """验证已抓取的省级发改委 fixture 可读取"""
    from src.data_collection.electricity_prices import load_fixture, list_fixtures, get_fixture_log
    log = get_fixture_log()
    assert 'results' in log
    # 至少有 3 个成功抓取的 fixture
    df = list_fixtures()
    assert df['has_fixture'].sum() >= 3

    # 具体检查 3 个成功省份
    for prov in ['北京', '上海', '宁夏']:
        content = load_fixture(prov)
        assert content is not None, f"{prov} fixture 缺失"
        assert '发改' in content or '价格' in content or 'SiteName' in content


def test_price_extraction():
    """验证从文本中提取价格数字"""
    from src.data_collection.electricity_prices import extract_price_hints
    sample = "工商业电价调整为 0.65 元/kWh，居民电价 0.4883元/千瓦时"
    prices = extract_price_hints(sample)
    assert 0.65 in prices


if __name__ == '__main__':
    test_load_reference_data(); print('✓ load_reference_data')
    test_site_scoring(); print('✓ site_scoring')
    test_irr_calculation(); print('✓ irr_calculation')
    test_revenue_stream(); print('✓ revenue_stream')
    test_cost_stream(); print('✓ cost_stream')
    test_fixtures_available(); print('✓ fixtures_available')
    test_price_extraction(); print('✓ price_extraction')
    print('\n所有 smoke test 通过 ✓')
