from pathlib import Path

# paths are relative to the repo root, so it runs on any machine
ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "space_missions_clean.csv"
FIG = ROOT / "figures"

import pandas as pd
import numpy as np
from scipy.stats import linregress, ttest_ind

df = pd.read_csv(DATA)
df_price = df[df['Price'].notna()].copy()
df_price['Year'] = df_price['Year'].astype(int)

is_spacex = df_price['Company'] == 'SpaceX'
era_order = ['Cold War', 'Post-Cold War', 'Early Commercial', 'New Space']

print("=" * 60)
print("Median Launch Cost by Era (excl. SpaceX)")
print("=" * 60)
for era in era_order:
    sub = df_price[(df_price['Era'] == era) & (~is_spacex)]['Price']
    print(f"{era:20s}  Median=${sub.median():.1f}M  "
          f"n={len(sub)}  P25=${sub.quantile(0.25):.1f}M  P75=${sub.quantile(0.75):.1f}M")

cw_median = df_price[(df_price['Era'] == 'Cold War') & (~is_spacex)]['Price'].median()
ec_median = df_price[(df_price['Era'] == 'Early Commercial') & (~is_spacex)]['Price'].median()
ns_median = df_price[(df_price['Era'] == 'New Space') & (~is_spacex)]['Price'].median()

print(f"\nCold War → New Space median cost: ${cw_median:.0f}M → ${ns_median:.0f}M")
print(f"Reduction: {(cw_median - ns_median) / cw_median * 100:.1f}%")
print(f"\nEarly Commercial → New Space median cost: ${ec_median:.0f}M → ${ns_median:.0f}M")
print(f"Reduction: {(ec_median - ns_median) / ec_median * 100:.1f}%")

print("\n" + "=" * 60)
print("Log-scale Linear Regression: Cost over Time")
print("(excl. SpaceX and outliers >$500M)")
print("=" * 60)
mask = (~is_spacex) & (df_price['Price'] < 500)
sub = df_price[mask].copy()
sub['logPrice'] = np.log10(sub['Price'])
sl, ic, r, p, _ = linregress(sub['Year'], sub['logPrice'])
annual_pct = (10**sl - 1) * 100
print(f"Slope: {sl:.4f} log10/yr")
print(f"R²: {r**2:.3f}")
print(f"p-value: {p:.4f}")
print(f"Interpretation: avg. {annual_pct:.1f}% change in cost per year")

print("\n" + "=" * 60)
print("Independent t-test: Early Commercial vs New Space cost")
print("(excl. SpaceX and outliers >$500M)")
print("=" * 60)
ec = df_price[(df_price['Era'] == 'Early Commercial') & (~is_spacex) & (df_price['Price'] < 500)]['Price']
ns = df_price[(df_price['Era'] == 'New Space') & (~is_spacex) & (df_price['Price'] < 500)]['Price']
t, p_val = ttest_ind(ec, ns)
print(f"Early Commercial: mean=${ec.mean():.1f}M  n={len(ec)}")
print(f"New Space:        mean=${ns.mean():.1f}M  n={len(ns)}")
print(f"t-statistic: {t:.2f}")
print(f"p-value: {p_val:.4f}")
print(f"Result: {'Statistically significant (p<0.05)' if p_val < 0.05 else 'Not significant'}")

print("\n" + "=" * 60)
print("SpaceX Cost Summary")
print("=" * 60)
spx = df_price[is_spacex]
print(f"Median: ${spx['Price'].median():.1f}M")
print(f"Min: ${spx['Price'].min():.1f}M")
print(f"Max: ${spx['Price'].max():.1f}M")
print(f"n: {len(spx)}")