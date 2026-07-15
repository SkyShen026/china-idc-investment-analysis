"""中国地图可视化：IDC 选址热力图

输出 HTML 交互地图，可直接放 GitHub Pages 展示。
"""
from __future__ import annotations
from pathlib import Path
import pandas as pd


def plot_idc_opportunity_map(scored_df: pd.DataFrame,
                              output_html: str | Path,
                              center: tuple = (35.0, 105.0),
                              zoom: int = 4) -> Path:
    """
    用 Folium 绘制中国 IDC 投资机会热力图

    Parameters
    ----------
    scored_df : 含 latitude, longitude, composite_score, city 的 DataFrame
    output_html : 输出 HTML 路径

    Returns
    -------
    Path 输出文件路径
    """
    import folium
    from folium.plugins import MarkerCluster

    m = folium.Map(
        location=center,
        zoom_start=zoom,
        tiles='cartodbpositron',
    )

    # 综合分 → 颜色
    def score_to_color(score: float) -> str:
        if score >= 80:
            return '#1a9850'  # 深绿（强烈推荐）
        elif score >= 65:
            return '#91cf60'  # 浅绿
        elif score >= 50:
            return '#fee08b'  # 黄
        elif score >= 35:
            return '#fc8d59'  # 橙
        else:
            return '#d73027'  # 红（不推荐）

    for _, row in scored_df.iterrows():
        popup_html = f"""
        <div style="font-family: Arial; font-size: 12px; min-width: 220px;">
            <h4 style="margin: 0 0 6px 0;">{row['city']} ({row['province']})</h4>
            <b>综合评分</b>: {row['composite_score']:.1f} / 100<br>
            <b>城市等级</b>: {row.get('tier', '-')}<br>
            <hr style="margin: 5px 0;">
            <b>电价</b>: ¥{row.get('power_price', 0):.3f}/kWh<br>
            <b>政策节点</b>: {int(row.get('policy_score', 0))}<br>
            <b>气候散热</b>: {int(row.get('cooling_score', 0))}/10<br>
            <b>距需求</b>: {int(row.get('demand_proximity_raw', 0))} km
        </div>
        """
        folium.CircleMarker(
            location=[row['latitude'], row['longitude']],
            radius=8 + row['composite_score'] / 10,
            color=score_to_color(row['composite_score']),
            fill=True,
            fill_color=score_to_color(row['composite_score']),
            fill_opacity=0.7,
            popup=folium.Popup(popup_html, max_width=280),
            tooltip=f"{row['city']}: {row['composite_score']:.0f}",
        ).add_to(m)

    # 图例
    legend_html = """
    <div style="position: fixed; bottom: 30px; left: 30px;
                background: white; padding: 10px 14px;
                border: 1px solid #ccc; border-radius: 4px;
                font-family: Arial; font-size: 12px; z-index: 9999;">
        <b style="font-size: 13px;">综合投资评分</b><br>
        <span style="color: #1a9850;">●</span> 80+ 强烈推荐<br>
        <span style="color: #91cf60;">●</span> 65-80 推荐<br>
        <span style="color: #fee08b;">●</span> 50-65 中性<br>
        <span style="color: #fc8d59;">●</span> 35-50 谨慎<br>
        <span style="color: #d73027;">●</span> &lt;35 不推荐
    </div>
    """
    m.get_root().html.add_child(folium.Element(legend_html))

    output_html = Path(output_html)
    output_html.parent.mkdir(parents=True, exist_ok=True)
    m.save(str(output_html))
    return output_html


if __name__ == '__main__':
    from src.model.site_score import load_all_data, score_cities

    data = load_all_data()
    scored = score_cities(data['cities'], data['power'], data['climate'], data['nodes'])

    out = Path(__file__).parent.parent.parent / 'outputs' / 'china_idc_opportunity_map.html'
    plot_idc_opportunity_map(scored, out)
    print(f"地图已生成: {out}")
