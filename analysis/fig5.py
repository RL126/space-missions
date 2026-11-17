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

top_companies = df['Company'].value_counts().nlargest(10).index.tolist()
df['CompanyGroup'] = df['Company'].apply(
    lambda x: x if x in top_companies else 'Others')

# 顺序：发射量多的在上，Others 最下
order = (df[df['CompanyGroup'] != 'Others']
         .groupby('CompanyGroup').size()
         .sort_values(ascending=True).index.tolist())
order = ['Others'] + order  # Others 最下面

color_map = {
    'RVSN USSR':      '#E74C3C',
    'CASC':           '#2471A3',
    'Arianespace':    '#1ABC9C',
    'General Dynamics':'#E67E22',
    'VKS RF':         '#8E44AD',
    'NASA':           '#2ECC71',
    'SpaceX':         '#F1C40F',
    'US Air Force':   '#154360',
    'ULA':            '#E91E8C',
    'Boeing':         '#00BCD4',
    'Others':         '#BDC3C7',
}

np.random.seed(42)
y_map = {co: i for i, co in enumerate(order)}

fig, ax = plt.subplots(figsize=(18, 8))
fig.subplots_adjust(left=0.14, right=0.96, top=0.85, bottom=0.10)

for co in order:
    sub = df[df['CompanyGroup'] == co]
    y_base = y_map[co]
    jitter = np.random.uniform(-0.38, 0.38, size=len(sub))
    marker = 'D' if co == 'SpaceX' else 'o'   # ← SpaceX 用菱形，其余圆点
    size   = 14 if co == 'SpaceX' else 7       # ← 菱形视觉偏小，放大一点
    ax.scatter(sub['Year'], y_base + jitter,
               color=color_map[co], s=size, marker=marker,
               alpha=0.75, linewidths=0, zorder=3)

# 时代背景色块
era_spans = [
    ('Cold War',         1957, 1991, '#FBF0F4'),
    ('Post-Cold War',    1992, 2000, '#EEF5FB'),
    ('Early Commercial', 2001, 2015, '#F0FAF0'),
    ('New Space',        2016, 2022, '#FEFAE8'),
]
for era, x0, x1, bg in era_spans:
    ax.axvspan(x0 - 0.5, x1 + 0.5, color=bg, alpha=0.85, zorder=0)

# 时代分隔线
for _, x0, _, _ in era_spans[1:]:
    ax.axvline(x0 - 0.5, color='#CCCCCC', linewidth=1,
               linestyle='--', zorder=1)

# 时代标签放在图顶部上方
era_label_x = [
    (1957 + 1991) / 2,
    (1992 + 2000) / 2,
    (2001 + 2015) / 2,
    (2016 + 2022) / 2,
]
for (era, x0, x1, _), lx in zip(era_spans, era_label_x):
    frac = (lx - 1956.5) / (2023.5 - 1956.5)
    ax.text(frac, 1.01, era,
            transform=ax.transAxes,
            ha='center', va='bottom', fontsize=8.5,
            color='#999999', style='italic')

# 轴
ax.set_yticks(range(len(order)))
ax.set_yticklabels(order, fontsize=10)
ax.set_xlim(1956, 2023)
ax.set_ylim(-0.7, len(order) - 0.3)
ax.set_xlabel('Year', fontsize=11)
ax.set_title('Every Launch, 1957–2022\nEach dot represents one mission, colored by company',
             fontsize=14, fontweight='bold', pad=20)

ax.grid(axis='x', linestyle='--', alpha=0.2, zorder=0)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.spines['left'].set_visible(False)
ax.tick_params(axis='y', left=False)

# 右侧 n= 标注
for co in order:
    n = len(df[df['CompanyGroup'] == co])
    ax.text(2023.5, y_map[co], f'n={n}',
            va='center', fontsize=8, color='#AAAAAA')

plt.savefig(FIG / 'fig5_dotstrip.png',
            dpi=150, bbox_inches='tight')
print("fig5 保存完成")