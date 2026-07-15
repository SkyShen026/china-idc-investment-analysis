"""分析图表：敏感性分析、对比柱状图、瀑布图"""
from __future__ import annotations
from pathlib import Path
import pandas as pd
import numpy as np


def plot_top_cities_bar(scored_df: pd.DataFrame, top_n: int = 10,
                         output_path: str | Path = None):
    """Top N 城市综合分柱状图"""
    import plotly.express as px
    df = scored_df.head(top_n).copy()
    fig = px.bar(
        df, x='composite_score', y='city',
        orientation='h',
        color='composite_score',
        color_continuous_scale='RdYlGn',
        title=f'Top {top_n} 数据中心选址综合评分',
        labels={'composite_score': '综合评分 (0-100)', 'city': '城市'},
        text=df['composite_score'].round(1),
    )
    fig.update_layout(yaxis={'categoryorder': 'total ascending'}, height=500)
    if output_path:
        fig.write_html(str(output_path))
    return fig


def plot_irr_sensitivity(base_params: dict,
                          variable: str,
                          range_values: list,
                          output_path: str | Path = None):
    """
    IRR 单变量敏感性分析

    Parameters
    ----------
    base_params : 基准参数 dict（传给 calculate_idc_irr）
    variable : 要扫描的变量名（如 'electricity_price'）
    range_values : 该变量的取值范围
    """
    import plotly.graph_objects as go
    from src.model.irr import calculate_idc_irr

    irrs = []
    for v in range_values:
        params = base_params.copy()
        params[variable] = v
        try:
            r = calculate_idc_irr(**params)
            irrs.append(r['irr'])
        except Exception:
            irrs.append(np.nan)

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=range_values, y=[i * 100 for i in irrs],
        mode='lines+markers',
        line=dict(width=3),
    ))
    fig.update_layout(
        title=f'IRR 对 {variable} 的敏感性',
        xaxis_title=variable,
        yaxis_title='IRR (%)',
        height=400,
    )
    if output_path:
        fig.write_html(str(output_path))
    return fig


def plot_tornado(base_irr: float, sensitivities: dict,
                  output_path: str | Path = None):
    """
    龙卷风图：多变量敏感性对 IRR 的影响

    sensitivities = {
        'electricity_price': (low_irr, high_irr),
        'pue': (low_irr, high_irr),
        ...
    }
    """
    import plotly.graph_objects as go

    variables = list(sensitivities.keys())
    low_impacts = [sensitivities[v][0] - base_irr for v in variables]
    high_impacts = [sensitivities[v][1] - base_irr for v in variables]

    # 按总影响排序
    abs_impacts = [abs(l) + abs(h) for l, h in zip(low_impacts, high_impacts)]
    order = sorted(range(len(variables)), key=lambda i: abs_impacts[i])
    variables = [variables[i] for i in order]
    low_impacts = [low_impacts[i] * 100 for i in order]
    high_impacts = [high_impacts[i] * 100 for i in order]

    fig = go.Figure()
    fig.add_trace(go.Bar(y=variables, x=low_impacts, orientation='h',
                          name='下行', marker_color='#d73027'))
    fig.add_trace(go.Bar(y=variables, x=high_impacts, orientation='h',
                          name='上行', marker_color='#1a9850'))
    fig.update_layout(
        title=f'敏感性分析：变量对 IRR 的影响 (基准 IRR = {base_irr:.1%})',
        barmode='overlay',
        xaxis_title='IRR 变化 (pp)',
        height=400,
    )
    if output_path:
        fig.write_html(str(output_path))
    return fig
