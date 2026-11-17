from pathlib import Path

# paths are relative to the repo root, so it runs on any machine
ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "space_missions_clean.csv"
FIG = ROOT / "figures"

import json
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from collections import defaultdict
import geopandas as gpd

# 读取数据
with open(ROOT / "globe" / "launch_data.json", encoding='utf-8') as f:
    data = json.load(f)

# 聚合每个站点的总发射数和主阵营
site_info = {}
for r in data['records']:
    s = r['site']
    if s not in site_info:
        site_info[s] = {'lat': r['lat'], 'lng': r['lng'], 'count': 0, 'blocs': defaultdict(int)}
    site_info[s]['count'] += r['count']
    site_info[s]['blocs'][r['bloc']] += r['count']

bloc_colors = {
    'Soviet/Russia': '#E74C3C',
    'US Government': '#2471A3',
    'US Commercial': '#85C1E9',
    'China':         '#E67E22',
    'Joint Venture': '#8E44AD',
    'Other':         '#95A5A6',
}

def dot_size(count):
    if count <= 50:   return 40
    if count <= 200:  return 100
    if count <= 500:  return 220
    return 500

fig, ax = plt.subplots(figsize=(14, 7), facecolor='#0a0a1a')
ax.set_facecolor('#0d1b2a')
ax.set_xlim(-180, 180)
ax.set_ylim(-90, 90)

# ── 世界地图底图 ──────────────────────────────────────────────────
from geodatasets import get_path
world = gpd.read_file(get_path('naturalearth.land'))
world.plot(ax=ax,
           color='#1a2f45',
           edgecolor='#2a4a6a',
           linewidth=0.4,
           zorder=2)

# 经纬度网格线
for lon in range(-180, 181, 30):
    ax.axvline(lon, color='#1a2a3a', linewidth=0.4, zorder=1)
for lat in range(-90, 91, 30):
    ax.axhline(lat, color='#1a2a3a', linewidth=0.4, zorder=1)

# 绘制发射场圆点
for site, info in site_info.items():
    top_bloc = max(info['blocs'], key=info['blocs'].get)
    color = bloc_colors.get(top_bloc, '#95A5A6')
    size  = dot_size(info['count'])
    ax.scatter(info['lng'], info['lat'],
               s=size, c=color, alpha=0.88,
               zorder=5, linewidths=0.6, edgecolors='white')

# 标注前5大站点名称
top_sites = sorted(site_info.items(), key=lambda x: -x[1]['count'])[:5]
for site, info in top_sites:
    short = site.split(',')[0]
    ax.annotate(short, (info['lng'], info['lat']),
                xytext=(5, 5), textcoords='offset points',
                fontsize=6.5, color='white', alpha=0.85)

# 图例：阵营颜色
legend_patches = [mpatches.Patch(color=c, label=l) for l, c in [
    ('Soviet/Russia', '#E74C3C'),
    ('US Government', '#2471A3'),
    ('US Commercial', '#85C1E9'),
    ('China',         '#E67E22'),
    ('Other',         '#95A5A6'),
]]
size_legend = [
    plt.scatter([], [], s=40,  c='#aaa', alpha=0.8, label='1–50'),
    plt.scatter([], [], s=100, c='#aaa', alpha=0.8, label='51–200'),
    plt.scatter([], [], s=220, c='#aaa', alpha=0.8, label='201–500'),
    plt.scatter([], [], s=500, c='#aaa', alpha=0.8, label='500+'),
]

l1 = ax.legend(handles=legend_patches, loc='lower left', fontsize=8,
               framealpha=0.4, facecolor='#0a0a1a', labelcolor='white',
               title='Bloc', title_fontsize=8)
l1.get_title().set_color('white')
l2 = ax.legend(handles=size_legend, loc='lower right', fontsize=8,
               framealpha=0.4, facecolor='#0a0a1a', labelcolor='white',
               title='Launch Count', title_fontsize=8)
l2.get_title().set_color('white')
ax.add_artist(l1)

ax.set_xlabel('Longitude', color='#666', fontsize=8)
ax.set_ylabel('Latitude',  color='#666', fontsize=8)
ax.tick_params(colors='#555', labelsize=7)
for spine in ax.spines.values():
    spine.set_edgecolor('#1a2a3a')

ax.set_title('Global Space Launch Sites 1957–2022  (2D Equirectangular Projection)',
             color='white', fontsize=12, pad=10)

plt.tight_layout()
plt.savefig(FIG / 'launch_sites_2d.png', dpi=150, bbox_inches='tight', facecolor='#0a0a1a')
plt.show()
print("saved: launch_sites_2d.png")