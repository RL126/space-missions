from pathlib import Path

# paths are relative to the repo root, so it runs on any machine
ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "space_missions_clean.csv"
FIG = ROOT / "figures"

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
from matplotlib.ticker import FuncFormatter

# ── 读取数据 ───────────────────────────────────────────────────────────────
df = pd.read_csv(DATA)
df_price = df[df['Price'].notna()].copy()
df_price['Year'] = df_price['Year'].astype(int)

is_spacex = df_price['Company'] == 'SpaceX'
era_order = ['Cold War', 'Post-Cold War', 'Early Commercial', 'New Space']

rows_data = []
for era in era_order:
    sub = df_price[(df_price['Era'] == era) & (~is_spacex)]['Price']
    rows_data.append({'label': era, 'p25': sub.quantile(0.25),
                      'median': sub.median(), 'p75': sub.quantile(0.75), 'n': len(sub)})

spx = df_price[is_spacex]['Price']
rows_data.append({'label': 'SpaceX (2006–2022)', 'p25': spx.quantile(0.25),
                  'median': spx.median(), 'p75': spx.quantile(0.75), 'n': len(spx)})

stats = pd.DataFrame(rows_data)

# ── Okabe-Ito 色盲友好配色 ─────────────────────────────────────────────────
# 原配色依赖红绿区分（粉红/红/绿/橙），红绿色盲（男性约8%）无法区分
# Okabe-Ito 改用蓝色分量 + 亮度差异，五色在各类色觉缺陷下均可区分
era_colors_cb = {
    'Cold War':            '#0072B2',   # 深蓝
    'Post-Cold War':       '#56B4E9',   # 天蓝
    'Early Commercial':    '#009E73',   # 绿
    'New Space':           '#E69F00',   # 橙
    'SpaceX (2006–2022)':  '#D55E00',   # 朱红
}

# ── 绘图 ───────────────────────────────────────────────────────────────────
n_rows = len(stats)
y_pos = list(range(n_rows - 1, -1, -1))

fig, ax = plt.subplots(figsize=(12, 7))
fig.subplots_adjust(left=0.24, right=0.84, top=0.84, bottom=0.18)

for i, row in stats.iterrows():
    y = y_pos[i]
    c = era_colors_cb[row['label']]
    p25, med, p75 = row['p25'], row['median'], row['p75']
    is_cw  = row['label'] == 'Cold War'
    is_spx = 'SpaceX' in row['label']

    # 连接线
    ax.plot([p25, p75], [y, y], color=c, linewidth=4,
            alpha=0.45, zorder=2, solid_capstyle='round')

    # P25 端点
    ax.scatter(p25, y, color=c, s=100, zorder=4,
               edgecolors='white', linewidths=1.2)

    # 中位数大圆
    ax.scatter(med, y, color=c, s=300, zorder=5,
               edgecolors='white', linewidths=1.8)

    # P75 端点（Cold War 中位=P75 重叠跳过；SpaceX 区间极窄跳过）
    if not is_cw and not is_spx:
        ax.scatter(p75, y, color=c, s=100, zorder=4,
                   edgecolors='white', linewidths=1.2)

    # P25 左侧标注
    ax.text(p25 * 0.87, y, f"${p25:.0f}M",
            ha='right', va='center', fontsize=8.5, color='#555555')

    if is_cw:
        # Cold War：中位=P75，标注右侧下方，附加偏差说明
        ax.text(med * 1.05, y - 0.20,
                f"${med:.0f}M  (median = P75)\nskewed: mostly gov. missions",
                ha='left', va='top', fontsize=7.8,
                color=c, fontweight='bold', zorder=6, linespacing=1.6)

    elif is_spx:
        # SpaceX：中位标注移到右侧，避免压在圆点上
        ax.text(med * 1.18, y, f"${med:.0f}M",
                ha='left', va='center', fontsize=9.5,
                fontweight='bold', color=c, zorder=6)

    else:
        # 普通时代：中位标注上方，P75 标注右侧
        ax.text(med, y + 0.30, f"${med:.0f}M",
                ha='center', va='bottom', fontsize=9.5,
                fontweight='bold', color=c, zorder=6)
        ax.text(p75 * 1.13, y, f"${p75:.0f}M",
                ha='left', va='center', fontsize=8.5, color='#555555')

# 分隔线（Era vs SpaceX）
ax.axhline(0.5, color='#CCCCCC', linewidth=1, linestyle='--', zorder=1)

# ── Y 轴 ───────────────────────────────────────────────────────────────────
ylabels = [f"{row['label']}   n={row['n']}" for _, row in stats.iterrows()]
ax.set_yticks(y_pos)
ax.set_yticklabels(ylabels, fontsize=10.5)
ax.tick_params(axis='y', left=False)
for label, tick in zip(ylabels, ax.yaxis.get_ticklabels()):
    if 'SpaceX' in label:
        tick.set_color(era_colors_cb['SpaceX (2006–2022)'])
        tick.set_fontweight('bold')

# ── X 轴 ───────────────────────────────────────────────────────────────────
ax.set_xscale('log')
ax.set_xlim(8, 1800)
ax.set_ylim(-0.7, n_rows - 0.3)
ax.xaxis.set_major_formatter(FuncFormatter(lambda x, _: f'${x:,.0f}M'))
ax.tick_params(axis='x', labelsize=9)

for xv in [10, 100, 1000]:
    ax.axvline(xv, color='#EEEEEE', linewidth=1, zorder=0)

# ── 标题 & 副标题 ──────────────────────────────────────────────────────────
ax.set_xlabel('Launch Price (Million USD, log scale)', fontsize=11)
ax.set_title('Launch Cost Distribution by Era', fontsize=14,
             fontweight='bold', pad=14)


# ── 网格 & 边框 ────────────────────────────────────────────────────────────
ax.grid(axis='x', which='major', linestyle='--', alpha=0.25)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.spines['left'].set_visible(False)

# ── 图例 ───────────────────────────────────────────────────────────────────
ax.text(0.99, 0.02, "● Median    ━  P25–P75 range",
        transform=ax.transAxes, ha='right', va='bottom',
        fontsize=8.5, color='#888888',
        bbox=dict(boxstyle='round,pad=0.3', facecolor='white',
                  edgecolor='#DDDDDD', alpha=0.85))

# ── Figure caption ─────────────────────────────────────────────────────────
caption = (
    "Figure 3. Launch cost distribution by era (excluding outliers > $500M and SpaceX). "
    "Circles denote median price; horizontal lines span the interquartile range (P25–P75). "
    "X-axis uses log scale to accommodate a three-order-of-magnitude price range ($7M–$5,000M). "
    "Cold War median equals P75, indicating data are skewed toward large government missions (n=101). "
    "Colours follow the Okabe-Ito palette to ensure accessibility for colour-vision deficiency "
    "(Okabe & Ito, 2008)."
)
fig.text(0.5, 0.01, caption, ha='center', va='bottom',
         fontsize=8, color='#444444', wrap=True, style='italic',
         bbox=dict(boxstyle='round,pad=0.4', facecolor='#F9F9F9',
                   edgecolor='#DDDDDD', alpha=0.7))

# ── 保存 ───────────────────────────────────────────────────────────────────
plt.savefig(FIG / 'fig3_dumbbell.png',
            dpi=150, bbox_inches='tight')
print("保存完成")