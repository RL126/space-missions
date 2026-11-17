from pathlib import Path

# paths are relative to the repo root, so it runs on any machine
ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "space_missions_clean.csv"
FIG = ROOT / "figures"

import pandas as pd
import numpy as np
df = pd.read_csv(ROOT / "data" / "space_missions.csv", encoding="latin-1")
# ── 1. 日期解析 ──────────────────────────────────────────
df['Date'] = pd.to_datetime(df['Date'])
df['Year'] = df['Date'].dt.year
# ── 2. 价格字段清洗 ──────────────────────────────────────
df['Price'] = df['Price'].astype(str).str.replace(',', '').str.strip()
df['Price'] = pd.to_numeric(df['Price'], errors='coerce')
# ── 3. 从Location提取国家 ────────────────────────────────
df['Country'] = df['Location'].str.split(',').str[-1].str.strip()
country_fix = {
    'Kazakhstan': 'Kazakhstan',
    'Russia': 'Russia',
    'USA': 'USA',
    'French Guiana': 'France',
    'China': 'China',
    'Japan': 'Japan',
    'India': 'India',
    'New Zealand': 'New Zealand',
    'Kenya': 'Kenya',
    'Iran': 'Iran',
    'Israel': 'Israel',
    'Marshall Islands': 'Marshall Islands',
    'Yellow Sea': 'China',
    'Barents Sea': 'Russia',
}
df['Country'] = df['Country'].map(lambda x: country_fix.get(x, x))
# ── 4. 阵营分组 ──────────────────────────────────────────
soviet_russian = [
    'RVSN USSR', 'VKS RF', 'Roscosmos', 'MHI',
    'Kosmotras', 'Eurockot', 'Starsem', 'ISA',
    'Land Launch', 'KARI',
]
us_government = [
    'NASA', 'US Air Force', 'US Navy', 'AMBA',
    'Douglas', 'Sandia', 'DARPA',
]
us_commercial = [
    'SpaceX', 'ULA', 'Boeing', 'Martin Marietta',
    'General Dynamics', 'Northrop', 'Lockheed',
    'Rocket Lab', 'Blue Origin',
    'Hughes', 'OSC', 'Orbital', 'Virgin Orbit',
    'Firefly', 'Astra', 'ABL',
]
joint_venture = ['ILS', 'Sea Launch']
china = ['CASC', 'ExPace', 'Expace', 'Galactic Energy', 'iSpace', 'LandSpace']
europe = ['Arianespace', 'ESA', 'ISRO']
def assign_bloc(company):
    if company in soviet_russian:
        return 'Soviet/Russia'
    elif company in us_government:
        return 'US Government'
    elif company in us_commercial:
        return 'US Commercial'
    elif company in joint_venture:
        return 'Joint Venture'
    elif company in china:
        return 'China'
    elif company in europe:
        return 'Other'
    else:
        return 'Other'
df['Bloc'] = df['Company'].apply(assign_bloc)
# ── 5. 任务状态简化 ──────────────────────────────────────
df['Success'] = df['MissionStatus'].apply(
    lambda x: 1 if x == 'Success' else 0
)
# ── 6. 时代分组 ──────────────────────────────────────────
def assign_era(year):
    if year <= 1991:
        return 'Cold War'
    elif year <= 2000:
        return 'Post-Cold War'
    elif year <= 2015:
        return 'Early Commercial'
    else:
        return 'New Space'
df['Era'] = df['Year'].apply(assign_era)
# ── 7. 输出结果 ──────────────────────────────────────────
print("清洗完成，数据概况：")
print(f"总行数: {len(df)}")
print(f"\nBloc分布:")
print(df['Bloc'].value_counts())
print(f"\nEra分布:")
print(df['Era'].value_counts())
print(f"\nCountry分布 (top 10):")
print(df['Country'].value_counts().head(10))
print(f"\nPrice非空数量: {df['Price'].notna().sum()} / {len(df)}")
print(f"\n年份范围: {df['Year'].min()} - {df['Year'].max()}")
df.to_csv(DATA, index=False)
print("\n已保存到 space_missions_clean.csv")