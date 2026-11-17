from pathlib import Path

# paths are relative to the repo root, so it runs on any machine
ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "space_missions_clean.csv"
FIG = ROOT / "figures"

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
from scipy.stats import linregress

# ── 读取数据 ──────────────────────────────────────────────
df = pd.read_csv(DATA)
df_price = df[df['Price'].notna()].copy()
df_price['Year'] = df_price['Year'].astype(int)

era_order  = ['Cold War', 'Post-Cold War', 'Early Commercial', 'New Space']
era_ranges = {
    'Cold War':         (1957, 1991),
    'Post-Cold War':    (1992, 2000),
    'Early Commercial': (2001, 2015),
    'New Space':        (2016, 2022),
}
era_colors = {
    'Cold War':         '#C9768F',
    'Post-Cold War':    '#5A9EC9',
    'Early Commercial': '#5AAE6E',
    'New Space':        '#E0A030',
}
era_bg = {
    'Cold War':         '#FBF0F4',
    'Post-Cold War':    '#EEF5FB',
    'Early Commercial': '#F0FAF0',
    'New Space':        '#FEFAE8',
}

is_spacex = df_price['Company'] == 'SpaceX'

# ── log 回归（排除 Energiya $5000M 超级离群）────────────
df_log = df_price.copy()
df_log['logPrice'] = np.log10(df_log['Price'])
mask_main = df_log['Price'] < 2000

sl, ic, r, p, _ = linregress(df_log.loc[mask_main, 'Year'],
                              df_log.loc[mask_main, 'logPrice'])

spx_mask = is_spacex & mask_main
sl2 = ic2 = r2 = None
if spx_mask.sum() >= 3:
    sl2, ic2, r2, _, _ = linregress(df_log.loc[spx_mask, 'Year'],
                                    df_log.loc[spx_mask, 'logPrice'])

# ── 画布 ──────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(14, 7))

# 时代背景色块 + 标签
for era, (yr0, yr1) in era_ranges.items():
    ax.axvspan(yr0 - 0.5, yr1 + 0.5, color=era_bg[era], zorder=0, alpha=0.9)
    ax.text((yr0 + yr1) / 2, 6000,
            era.replace(' ', '\n'), ha='center', va='top',
            fontsize=8.5, color='#999999', style='italic', zorder=1)

# 非SpaceX 散点（按时代着色）
for era in era_order:
    mask = (~is_spacex) & (df_price['Era'] == era)
    sub = df_price[mask]
    ax.scatter(sub['Year'], sub['Price'],
               color=era_colors[era], s=55, alpha=0.70,
               edgecolors='white', linewidths=0.5, zorder=3,
               label=era)

# SpaceX 散点
spx = df_price[is_spacex]
ax.scatter(spx['Year'], spx['Price'],
           color='#C0392B', s=80, alpha=0.92, marker='D',
           edgecolors='white', linewidths=0.6,
           label='SpaceX', zorder=5)

# 整体趋势线
x_line = np.linspace(1964, 2022, 300)
y_line = 10 ** (sl * x_line + ic)
ax.plot(x_line, y_line,
        color='#2C3E50', linewidth=2, linestyle='--', alpha=0.65,
        label=f'Overall trend  R²={r**2:.2f}', zorder=4)

# SpaceX 趋势线
if sl2 is not None:
    spx_years = df_log.loc[spx_mask, 'Year']
    x2 = np.linspace(spx_years.min(), spx_years.max(), 200)
    y2 = 10 ** (sl2 * x2 + ic2)
    ax.plot(x2, y2,
            color='#C0392B', linewidth=2, linestyle='-.', alpha=0.75,
            label=f'SpaceX trend  R²={r2**2:.2f}', zorder=4)

# 关键标注
annotations = [
    (1967, 1160,  'Saturn V\n$1,160M',      (1970, 1700)),
    (1988, 5000,  'Energiya/Buran\n$5,000M', (1981, 3800)),
    (2010, 59.5,  'Falcon 9 debut\n$59.5M',  (2006, 32)),
    (2018, 90,    'Falcon Heavy\n$90M',       (2019.5, 150)),
]
for yr, price, label, (tx, ty) in annotations:
    ax.annotate(label,
                xy=(yr, price), xytext=(tx, ty),
                fontsize=7.5, color='#333333',
                arrowprops=dict(arrowstyle='->', color='#AAAAAA', lw=1),
                zorder=6)

# ── Log scale & 格式 ─────────────────────────────────────
ax.set_yscale('log')
ax.set_xlim(1963, 2023)
ax.set_ylim(3, 9000)

from matplotlib.ticker import FuncFormatter, LogLocator
ax.yaxis.set_major_locator(LogLocator(base=10, numticks=8))
ax.yaxis.set_major_formatter(FuncFormatter(lambda y, _: f'${y:,.0f}M'))

ax.set_xlabel('Year', fontsize=12)
ax.set_ylabel('Launch Price (Million USD, log scale)', fontsize=12)
ax.set_title('Launch Costs Over Time (1957–2022)\n'
             'Commercial Competition & SpaceX Drive Down Prices',
             fontsize=14, fontweight='bold', pad=14)

ax.grid(which='major', axis='y', linestyle='--', alpha=0.35, zorder=1)
ax.grid(which='minor', axis='y', linestyle=':', alpha=0.15, zorder=1)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.legend(loc='lower left', fontsize=8.5, framealpha=0.92, ncol=2)

plt.tight_layout()
plt.savefig(FIG / 'fig3_cost_scatter.png',
            dpi=150, bbox_inches='tight')
print("保存完成")
print(f"有价格数据总数：{len(df_price)}  SpaceX：{is_spacex.sum()}")
print(f"整体趋势 R²={r**2:.3f}  斜率={sl:.4f} log10/yr")