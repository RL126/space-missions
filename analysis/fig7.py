from pathlib import Path

# paths are relative to the repo root, so it runs on any machine
ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "space_missions_clean.csv"
FIG = ROOT / "figures"


import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA

df = pd.read_csv(DATA)
df['Year'] = df['Year'].astype(int)

# ── 1. 特征工程：每个国家一行，构造 6 维特征 ──────────────────────────
# 先确认列名。Success 字段：1=成功，其余=失败
# Country 字段：图4用的那个国家列
# Price 字段：成本（部分缺失）

# 只保留发射量足够的国家，避免只发射过 1-2 次的国家干扰聚类
country_counts = df['Country'].value_counts()
valid_countries = country_counts[country_counts >= 5].index.tolist()
d = df[df['Country'].isin(valid_countries)].copy()

feat = pd.DataFrame(index=valid_countries)

# 特征1：总发射量（规模）
feat['total_launches'] = d.groupby('Country').size()

# 特征2：平均成功率（可靠性）
feat['success_rate'] = d.groupby('Country')['Success'].mean()

# 特征3：首次发射年份（入场早晚）
feat['first_year'] = d.groupby('Country')['Year'].min()

# 特征4：活跃跨度（持续性）
feat['active_span'] = d.groupby('Country')['Year'].max() - d.groupby('Country')['Year'].min()

# 特征5：新航天时代(2016+)发射占比（现代性）
d['is_newspace'] = (d['Year'] >= 2016).astype(int)
feat['newspace_ratio'] = d.groupby('Country')['is_newspace'].mean()


feat = feat.dropna()

print("Feature matrix:")
print(feat.round(2))
print(f"\nNumber of countries: {len(feat)}, Number of features: {feat.shape[1]}")

# ── 2. 标准化（聚类前必须做，否则发射量量级压过成功率）────────────────
X = StandardScaler().fit_transform(feat)

# ── 3. 选 k：肘部法 + 轮廓系数 ──────────────────────────────────────
from sklearn.metrics import silhouette_score
inertias, sils = [], []
k_range = range(2, min(7, len(feat)))
for k in k_range:
    km = KMeans(n_clusters=k, random_state=42, n_init=10).fit(X)
    inertias.append(km.inertia_)
    sils.append(silhouette_score(X, km.labels_))

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4))
ax1.plot(list(k_range), inertias, 'o-', color='#2471A3')
ax1.set_xlabel('k'); ax1.set_ylabel('Inertia'); ax1.set_title('Elbow Method')
ax1.grid(alpha=0.3)
ax2.plot(list(k_range), sils, 'o-', color='#E67E22')
ax2.set_xlabel('k'); ax2.set_ylabel('Silhouette'); ax2.set_title('Silhouette Score')
ax2.grid(alpha=0.3)
plt.tight_layout()
plt.savefig(FIG / 'fig7_choose_k.png',
            dpi=150, bbox_inches='tight')
# 轮廓系数
print("\nSilhouette scores by k:", dict(zip(k_range, np.round(sils, 3))))

# ── 4. 用最佳 k 做 K-means ─────────────────────────────────────────
best_k = k_range[int(np.argmax(sils))]   # 轮廓系数最高的 k
# 选定的 k
print(f"\nSelected k = {best_k} (highest silhouette score)")
km = KMeans(n_clusters=best_k, random_state=42, n_init=10).fit(X)
feat['cluster'] = km.labels_

# ── 5. PCA 降到 2D，把聚类结果画出来（biplot）──────────────────────
pca = PCA(n_components=2)
coords = pca.fit_transform(X)
evr = pca.explained_variance_ratio_
# PCA 方差
print(f"\nPC1 explained variance: {evr[0]:.1%}, PC2: {evr[1]:.1%}, cumulative: {evr.sum():.1%}")

fig, ax = plt.subplots(figsize=(12, 9))
palette = ['#0072B2', '#E69F00', '#009E73', '#CC79A7', '#CC3311', '#56B4E9']

for c in range(best_k):
    mask = km.labels_ == c
    ax.scatter(coords[mask, 0], coords[mask, 1],
               s=120, color=palette[c], alpha=0.75,
               edgecolors='white', linewidths=1.5,
               label=f'Cluster {c}', zorder=3)

# 国家名标注
for i, name in enumerate(feat.index):
    ax.annotate(name, (coords[i, 0], coords[i, 1]),
                xytext=(6, 4), textcoords='offset points',
                fontsize=9, color='#333333')

# 特征向量箭头（biplot：显示每个特征往哪个方向拉）
feat_names = [c for c in feat.columns if c != 'cluster']
loadings = pca.components_.T * np.sqrt(pca.explained_variance_)
scale = np.abs(coords).max() / np.abs(loadings).max() * 0.7
for i, fname in enumerate(feat_names):
    ax.arrow(0, 0, loadings[i, 0]*scale, loadings[i, 1]*scale,
             color='#888888', alpha=0.6, head_width=0.08, zorder=2)
    ax.text(loadings[i, 0]*scale*1.12, loadings[i, 1]*scale*1.12, fname,
            color='#555555', fontsize=8.5, ha='center', style='italic')

ax.axhline(0, color='#CCCCCC', linewidth=0.8, zorder=1)
ax.axvline(0, color='#CCCCCC', linewidth=0.8, zorder=1)
ax.set_xlabel(f'PC1 ({evr[0]:.1%} variance)', fontsize=11)
ax.set_ylabel(f'PC2 ({evr[1]:.1%} variance)', fontsize=11)
ax.set_title('Clustering of Spacefaring Nations by Launch Profile\n(K-means on 5, projected via PCA)',
             fontsize=13, fontweight='bold', pad=15)
ax.legend(loc='best', fontsize=10)
ax.grid(alpha=0.2)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
plt.tight_layout()
plt.savefig(FIG / 'fig7_country_clusters.png',
            dpi=150, bbox_inches='tight')

# ── 6. 打印每个簇有哪些国家 + 簇的平均画像（给你写解读用）──────────────
print("\nClustering Result")
for c in range(best_k):
    members = feat[feat['cluster'] == c].index.tolist()
    print(f"\nCluster {c}: {members}")
    print(feat[feat['cluster'] == c][feat_names].mean().round(2).to_dict())

print("\n保存完成：fig7_choose_k.png（选k）, fig7_country_clusters.png（聚类biplot）")