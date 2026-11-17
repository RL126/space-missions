from pathlib import Path

# paths are relative to the repo root, so it runs on any machine
ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "space_missions_clean.csv"
FIG = ROOT / "figures"

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

df = pd.read_csv(DATA)
df['Year'] = df['Year'].astype(int)

blocs = ['Soviet/Russia', 'US Government', 'US Commercial', 'China', 'Joint Venture', 'Other']

# ── Okabe-Ito 色盲友好配色 ─────────────────────────────────────────────────
# 原配色问题：
#   Soviet/Russia 红 (#C0392B) vs China 橙 (#E67E22) → 红绿色盲难以区分
#   Joint Venture 紫 vs Other 灰 → 蓝黄色盲难以区分
# 每个子图独立显示，颜色只需在六个之间互相可区分
bloc_colors = {
    'Soviet/Russia':  '#CC3311',   # 红（与China橙明显区分）
    'US Government':  '#0072B2',   # 深蓝
    'US Commercial':  '#56B4E9',   # 天蓝
    'China':          '#E69F00',   # 橙
    'Joint Venture':  '#CC79A7',   # 玫红
    'Other':          '#009E73',   # 绿
}

annual = df.groupby(['Year', 'Bloc']).size().unstack(fill_value=0)
for b in blocs:
    if b not in annual.columns:
        annual[b] = 0

years = annual.index

era_spans = [
    (1957, 1991, '#FBF0F4', 'Cold War'),
    (1992, 2000, '#EEF5FB', 'Post-Cold War'),
    (2001, 2015, '#F0FAF0', 'Early Commercial'),
    (2016, 2022, '#FEFAE8', 'New Space'),
]

fig, axes = plt.subplots(2, 3, figsize=(18, 9), sharex=True)
axes = axes.flatten()

for idx, bloc in enumerate(blocs):
    ax = axes[idx]
    c = bloc_colors[bloc]
    data = annual[bloc] if bloc in annual.columns else pd.Series(0, index=years)

    for x0, x1, bg, name in era_spans:
        ax.axvspan(x0 - 0.5, x1 + 0.5, color=bg, alpha=0.9, zorder=0)

    for x0, x1, _, _ in era_spans[1:]:
        ax.axvline(x0 - 0.5, color='#CCCCCC', linewidth=1, linestyle='--', zorder=1)

    ax.fill_between(years, data, color=c, alpha=0.25, zorder=2)
    ax.plot(years, data, color=c, linewidth=2, zorder=3)

    if data.max() > 0:
        peak_year = data.idxmax()
        peak_val = data.max()
        ax.annotate(f'{peak_val:.0f}',
                    xy=(peak_year, peak_val),
                    xytext=(0, 6), textcoords='offset points',
                    ha='center', fontsize=8.5, color=c, fontweight='bold')

    ax.set_title(bloc, fontsize=11, fontweight='bold', color=c, pad=8)
    ax.set_ylim(0, None)
    ax.set_xlim(1957, 2022)
    ax.grid(axis='y', linestyle='--', alpha=0.3)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

    ax.set_xticks([1960, 1970, 1980, 1990, 2000, 2010, 2020])
    ax.set_xticklabels(['1960', '1970', '1980', '1990', '2000', '2010', '2020'],
                       fontsize=8.5)
    ax.tick_params(axis='x', labelbottom=True)

    if idx % 3 == 0:
        ax.set_ylabel('Launches', fontsize=9)
    else:
        ax.set_ylabel('')

    for x0, x1, _, name in era_spans:
        mid = (x0 + x1) / 2
        ax.text(mid, -0.16, name,
                transform=ax.get_xaxis_transform(),
                ha='center', fontsize=7, color='#AAAAAA', style='italic')

fig.suptitle('Annual Space Launches by Bloc (1957–2022)',
             fontsize=14, fontweight='bold', y=1.01)

fig.suptitle('Annual Space Launches by Bloc (1957–2022)',
             fontsize=14, fontweight='bold', y=1.01)

fig.supxlabel('Year', fontsize=11, y=-0.02)  
plt.tight_layout(rect=[0, 0, 1, 1])
plt.savefig(FIG / 'fig1_small_multiples.png',
            dpi=150, bbox_inches='tight')
print("保存完成")