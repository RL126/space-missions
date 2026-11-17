from pathlib import Path

# paths are relative to the repo root, so it runs on any machine
ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "space_missions_clean.csv"
FIG = ROOT / "figures"

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Patch
from matplotlib.lines import Line2D

# ── 读取数据 ──────────────────────────────────────────────
df = pd.read_csv(DATA)

# ── 按年份计算 ────────────────────────────────────────────
annual = df.groupby('Year').agg(
    total=('Success', 'count'),
    success=('Success', 'sum')
).reset_index()
annual['success_rate'] = annual['success'] / annual['total'] * 100
annual['success_rate_smooth'] = annual['success_rate'].rolling(window=5, center=True, min_periods=1).mean()

# ── Era设置 ───────────────────────────────────────────────
era_spans = [
    (1957, 1991, '#FADBD8', 'Cold War'),
    (1992, 2000, '#D6EAF8', 'Post-Cold War'),
    (2001, 2015, '#D5F5E3', 'Early Commercial'),
    (2016, 2022, '#FEF9E7', 'New Space'),
]

era_bar_colors = annual['Year'].apply(lambda y:
    '#E8A89C' if y <= 1991 else
    '#85C1E9' if y <= 2000 else
    '#82E0AA' if y <= 2015 else
    '#F9E79F'
)

events = [
    (1957, 'Sputnik'),
    (1967, 'Apollo 1'),
    (1969, 'Moon Landing'),
    (1986, 'Challenger'),
    (1991, 'USSR Collapse'),
    (2003, 'Columbia'),
    (2015, 'Falcon 9\nReusability'),
]

fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10),
                                sharex=True,
                                gridspec_kw={'height_ratios': [1.2, 1], 'hspace': 0.08})

# ── 上图：发射数量 ────────────────────────────────────────
ax1.bar(annual['Year'], annual['total'],
        color=era_bar_colors, edgecolor='none', alpha=0.85, zorder=2)

for start, end, color, name in era_spans:
    ax1.axvspan(start, end, alpha=0.12, color=color, zorder=0)
for year, label in events:
    ax1.axvline(x=year, color='#7F8C8D', linestyle='--', linewidth=0.9, alpha=0.7, zorder=3)

ax1.set_ylabel('Number of Launches', fontsize=11)
ax1.set_title('Annual Launch Count & Mission Success Rate (1957–2022)',
              fontsize=14, fontweight='bold', pad=12)
ax1.grid(axis='y', linestyle='--', alpha=0.35, zorder=1)
ax1.spines['top'].set_visible(False)
ax1.spines['right'].set_visible(False)
ax1.set_xlim(1957, 2022)

legend_patches = [Patch(facecolor=c, alpha=0.85, label=n)
                  for _, _, c, n in era_spans]
ax1.legend(handles=legend_patches, loc='upper right',
           fontsize=8.5, framealpha=0.9, ncol=2)

# ── 下图：成功率，y轴压缩到80-100% ──────────────────────
for start, end, color, name in era_spans:
    ax2.axvspan(start, end, alpha=0.12, color=color, zorder=0)

ax2.plot(annual['Year'], annual['success_rate'],
         color='#2471A3', linewidth=0.8, alpha=0.35, zorder=3)
ax2.plot(annual['Year'], annual['success_rate_smooth'],
         color='#2471A3', linewidth=2.5, zorder=4)

# y轴压缩到60-100，让波动更明显
ax2.set_ylim(60, 102)

for i, (year, label) in enumerate(events):
    ax2.axvline(x=year, color='#7F8C8D', linestyle='--', linewidth=0.9, alpha=0.7, zorder=3)
    ypos = 75 if i % 2 == 0 else 67
    ax2.text(year + 0.4, ypos, label,
             fontsize=7.5, color='#2C3E50',
             bbox=dict(boxstyle='round,pad=0.25', fc='white', ec='none', alpha=0.85),
             va='bottom')

for start, end, color, name in era_spans:
    ax2.text((start + end) / 2, 61, name,
             ha='center', va='top', fontsize=8, color='gray', style='italic')

ax2.set_ylabel('Success Rate (%)', fontsize=11)
ax2.set_xlabel('Year', fontsize=11)
ax2.grid(axis='y', linestyle='--', alpha=0.35, zorder=1)
ax2.spines['top'].set_visible(False)
ax2.spines['right'].set_visible(False)

legend_elements = [
    Line2D([0], [0], color='#2471A3', linewidth=2.5, label='Success Rate (5yr avg)'),
    Line2D([0], [0], color='#2471A3', linewidth=0.8, alpha=0.35, label='Annual Success Rate'),
]
ax2.legend(handles=legend_elements, loc='lower left', fontsize=8.5, framealpha=0.9)

plt.savefig(FIG / 'fig2_success_rate.png', dpi=150, bbox_inches='tight')
print("成功率版本保存完成")