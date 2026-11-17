from pathlib import Path

# paths are relative to the repo root, so it runs on any machine
ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "space_missions_clean.csv"
FIG = ROOT / "figures"

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

df = pd.read_csv(DATA)
heatmap_data = df.groupby(['Country', 'Year']).size().unstack(fill_value=0)
top_countries = heatmap_data.sum(axis=1).nlargest(12).index
heatmap_data = heatmap_data.loc[top_countries]
heatmap_data = heatmap_data.loc[heatmap_data.sum(axis=1).sort_values(ascending=False).index]

data_log = np.log1p(heatmap_data.values)
years = list(heatmap_data.columns)
countries = list(heatmap_data.index)

fig, ax = plt.subplots(figsize=(18, 7))
fig.subplots_adjust(bottom=0.22, top=0.90)

im = ax.imshow(data_log, aspect='auto', cmap='YlOrRd',
               interpolation='bilinear')

# X轴：每5年一个刻度
tick_indices = [i for i, y in enumerate(years) if y % 5 == 0]
ax.set_xticks([i for i in tick_indices])
ax.set_xticklabels([years[i] for i in tick_indices], rotation=45,
                   ha='right', fontsize=9)

# Y轴
ax.set_yticks(range(len(countries)))
ax.set_yticklabels(countries, fontsize=10)

# 时代分隔线（图内白色虚线）
era_boundaries = [('Cold War', 1957, 1991),
                  ('Post-Cold War', 1992, 2000),
                  ('Early Commercial', 2001, 2015),
                  ('New Space', 2016, 2022)]

for era, start, end in era_boundaries:
    if start in years:
        x0 = years.index(start)
        ax.axvline(x=x0 - 0.5, color='white', linewidth=2,
                   linestyle='--', alpha=0.85)
    x_start = years.index(start) if start in years else 0
    x_end = years.index(end) if end in years else len(years) - 1
    mid = (x_start + x_end) / 2
    ax.text(mid, -0.8, era,
            ha='center', va='top', fontsize=8.5,
            color='white', style='italic', fontweight='bold',
            transform=ax.transData)

# Colorbar
cbar = plt.colorbar(im, ax=ax, pad=0.01)
cbar.set_label('Launch Count (log scale)', fontsize=10)
ticks_log = [0, np.log1p(1), np.log1p(5), np.log1p(10),
             np.log1p(30), np.log1p(100)]
cbar.set_ticks(ticks_log)
cbar.set_ticklabels(['0', '1', '5', '10', '30', '100'])

ax.set_title('Annual Launch Frequency by Country (1957–2022)',
             fontsize=14, fontweight='bold', pad=14)
ax.set_xlabel('Year', fontsize=11, labelpad=8)
ax.set_ylabel('Country', fontsize=11)

# ── Figure caption ─────────────────────────────────────────────────────────
# 说明设计决策：双线性插值 + log scale 的原因
caption = (
    "Figure 4. Annual launch frequency by country for the 12 most active nations (1957–2022). "
    "Colour encodes launch count on a log\u2009+\u20091 scale to prevent high-volume countries "
    "(USA, Russia) from obscuring trends in lower-volume nations. "
    "Bilinear interpolation is applied for visual smoothness; underlying data remain discrete annual counts. "
    "White dashed lines mark era boundaries. "
    "Kazakhstan launches originate primarily from Baikonur Cosmodrome, "
    "operated by the Soviet Union and subsequently Russia under lease."
)
fig.text(0.5, 0.01, caption, ha='center', va='bottom',
         fontsize=8, color='#444444', style='italic',
         wrap=True,
         bbox=dict(boxstyle='round,pad=0.4', facecolor='#F9F9F9',
                   edgecolor='#DDDDDD', alpha=0.7))

plt.savefig(FIG / 'fig4_heatmap.png',
            dpi=150, bbox_inches='tight')
print("fig4 保存完成")