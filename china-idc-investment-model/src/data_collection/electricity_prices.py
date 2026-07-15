"""电价数据采集模块

数据源分三层：
1. 参考数据（data/reference/provincial_power_price.csv） - 手工整理的电价基准，开箱即用
2. Fixture 快照（data/raw/electricity/fixtures/） - 已抓取的省级发改委页面快照
3. 实时抓取（download_drc_page） - 从各省发改委官网抓最新公告

工程现实：
- 各省发改委的反爬和 JS 渲染差异极大，2026-07 实测 8 个省首页只有 3 个直连能拿到
  可用内容（北京、上海、宁夏）
- 电价 PDF 格式各省不一，全自动解析准确率有限
- 推荐生产流程：脚本定期抓取 → LLM 或正则粗提 → 人工校对 → 入库
"""
from __future__ import annotations
import json
import re
from pathlib import Path
from datetime import datetime
import pandas as pd
import requests


ROOT = Path(__file__).parent.parent.parent
REF_FILE = ROOT / 'data' / 'reference' / 'provincial_power_price.csv'
FIXTURE_DIR = ROOT / 'data' / 'raw' / 'electricity' / 'fixtures'
RAW_DIR = ROOT / 'data' / 'raw' / 'electricity'


# 省级发改委首页 URL（2026-07 实测，标注了直连可用性）
PROVINCIAL_DRC_PAGES = {
    '北京':   {'url': 'https://fgw.beijing.gov.cn/',    'reachable': True,  'notes': '首页内容丰富'},
    '上海':   {'url': 'https://fgw.sh.gov.cn/',         'reachable': True,  'notes': '价格公告在 /fgw_jggl/'},
    '宁夏':   {'url': 'https://fzggw.nx.gov.cn/',       'reachable': True,  'notes': '首页内容较少'},
    '广东':   {'url': 'https://drc.gd.gov.cn/',         'reachable': False, 'notes': '需真实 UA + 代理'},
    '贵州':   {'url': 'https://fgw.guizhou.gov.cn/',    'reachable': False, 'notes': 'JS 渲染，用 Playwright'},
    '内蒙古': {'url': 'https://fgw.nmg.gov.cn/',        'reachable': False, 'notes': 'JS 渲染'},
    '甘肃':   {'url': 'https://fzgg.gansu.gov.cn/',     'reachable': False, 'notes': '需真实 UA'},
    '浙江':   {'url': 'https://fzggw.zj.gov.cn/',       'reachable': False, 'notes': 'JS 渲染'},
    '四川':   {'url': 'https://fgw.sc.gov.cn/',         'reachable': False, 'notes': '需真实 UA'},
    '河北':   {'url': 'http://hbdrc.hebei.gov.cn/',     'reachable': False, 'notes': '需真实 UA'},
}


DEFAULT_HEADERS = {
    'User-Agent': ('Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
                   'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'),
    'Accept': 'text/html,application/xhtml+xml',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
}


# ============ 参考数据 API ============

def load_reference_prices() -> pd.DataFrame:
    """加载 30 个省份的电价参考数据（开箱即用）"""
    return pd.read_csv(REF_FILE)


def find_cheapest_provinces(top_n: int = 5, column: str = 'data_center_special_price') -> pd.DataFrame:
    """电价最低 Top N"""
    df = load_reference_prices()
    return df.nsmallest(top_n, column)[
        ['province', 'industrial_price_yuan_per_kwh', 'data_center_special_price', 'source_note']
    ]


# ============ Fixture 数据 API ============

def load_fixture(province: str) -> str | None:
    """加载已抓取的省级发改委页面 fixture"""
    matches = list(FIXTURE_DIR.glob(f"{province.lower()}_*.md")) + \
              list(FIXTURE_DIR.glob(f"{province}_*.md"))
    if not matches:
        # 尝试按拼音匹配
        pinyin_map = {'北京': 'beijing', '上海': 'shanghai', '宁夏': 'ningxia',
                      '贵州': 'guizhou', '广东': 'guangdong'}
        if province in pinyin_map:
            matches = list(FIXTURE_DIR.glob(f"{pinyin_map[province]}_*.md"))
    if not matches:
        return None
    return matches[0].read_text(encoding='utf-8')


def get_fixture_log() -> dict:
    """加载抓取日志"""
    log_file = FIXTURE_DIR / 'fetch_log.json'
    if not log_file.exists():
        return {}
    return json.loads(log_file.read_text(encoding='utf-8'))


def list_fixtures() -> pd.DataFrame:
    """列出所有已抓取的 fixture"""
    log = get_fixture_log()
    results = log.get('results', {})
    rows = []
    for province, info in results.items():
        rows.append({
            'province': province,
            'status': info.get('status', 'unknown'),
            'has_fixture': 'fixture' in info,
            'note': info.get('note', info.get('policy_dir_found') or info.get('price_dir_found') or ''),
        })
    return pd.DataFrame(rows)


# ============ 实时抓取 ============

def download_drc_page(province: str, out_dir: Path = None) -> Path | None:
    """
    实时下载省级发改委首页

    实测（2026-07）8/10 省份的直连不通，返回 None 时说明需要用
    Playwright/Chrome MCP 或商业代理。此时应回落到 load_fixture()。
    """
    if province not in PROVINCIAL_DRC_PAGES:
        raise ValueError(f"未收录省份: {province}")

    conf = PROVINCIAL_DRC_PAGES[province]
    if not conf['reachable']:
        print(f"  ⚠ {province} 直连不可用（{conf['notes']}），"
              f"请使用 load_fixture('{province}') 加载快照")
        return None

    out_dir = out_dir or RAW_DIR
    out_dir.mkdir(parents=True, exist_ok=True)

    try:
        r = requests.get(conf['url'], headers=DEFAULT_HEADERS, timeout=15, verify=False)
        r.raise_for_status()
        out_file = out_dir / f"{province}_drc_{datetime.now():%Y%m%d}.html"
        out_file.write_bytes(r.content)
        print(f"  ✓ {province} → {out_file.name} ({len(r.content):,} bytes)")
        return out_file
    except Exception as e:
        print(f"  ✗ {province} 抓取失败: {e}")
        return None


def batch_download_reachable() -> list[Path]:
    """批量抓取所有已知可访问的省份"""
    results = []
    for province, conf in PROVINCIAL_DRC_PAGES.items():
        if conf['reachable']:
            f = download_drc_page(province)
            if f:
                results.append(f)
    return results


# ============ 价格提取（从 fixture / HTML） ============

PRICE_PATTERN = re.compile(r'(\d+\.\d{2,4})\s*元\s*/\s*(?:千瓦时|kWh)')


def extract_price_hints(text: str) -> list[float]:
    """从文本中粗提可能的电价数字（0.10-2.00 元/kWh 范围）"""
    prices = []
    for match in PRICE_PATTERN.finditer(text):
        try:
            v = float(match.group(1))
            if 0.1 <= v <= 2.0:
                prices.append(v)
        except (ValueError, IndexError, TypeError):
            continue
    return prices


def parse_pdf_price(pdf_path: Path) -> pd.DataFrame:
    """从电价 PDF 提取结构化数据（需要 pdfplumber）"""
    try:
        import pdfplumber
    except ImportError:
        print("pip install pdfplumber 后才能解析 PDF")
        return pd.DataFrame()

    rows = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            for tbl in page.extract_tables() or []:
                for row in tbl:
                    if row and any('工商业' in (c or '') for c in row):
                        rows.append(row)
    return pd.DataFrame(rows) if rows else pd.DataFrame()


if __name__ == '__main__':
    print("=== 数据中心专项电价最低 Top 5 ===")
    print(find_cheapest_provinces(5).to_string(index=False))

    print("\n=== 已抓取的 fixture 状态（2026-07 快照）===")
    print(list_fixtures().to_string(index=False))

    print("\n=== 上海 fixture 摘要 ===")
    sh = load_fixture('上海')
    if sh:
        # 只显示前 30 行
        print('\n'.join(sh.splitlines()[:30]))
