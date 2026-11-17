from pathlib import Path

# paths are relative to the repo root, so it runs on any machine
ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "space_missions_clean.csv"
FIG = ROOT / "figures"

import pandas as pd
import json

# 发射场坐标映射
site_coords = {
    'Plesetsk Cosmodrome, Russia': (62.9271, 40.5777),
    'Florida, USA': (28.5721, -80.6480),
    'Baikonur Cosmodrome, Kazakhstan': (45.9200, 63.3420),
    'California, USA': (34.7420, -120.5724),
    'French Guiana, France': (5.2368, -52.7697),
    'Jiuquan Satellite Launch Center, China': (40.9608, 100.2986),
    'Xichang Satellite Launch Center, China': (28.2463, 102.0264),
    'Kapustin Yar, Russia': (48.5740, 46.2520),
    'Tanegashima Space Center, Japan': (30.4011, 130.9750),
    'Satish Dhawan Space Centre, India': (13.7330, 80.2350),
    'Taiyuan Satellite Launch Center, China': (38.8490, 111.6080),
    'Uchinoura Space Center, Japan': (31.2510, 131.0820),
    'Virginia, USA': (37.9401, -75.4664),
    'Kiritimati Launch Area, Pacific Ocean': (1.8729, -157.4283),
    'Texas, USA': (28.5630, -97.1570),
    'Wenchang Satellite Launch Center, China': (19.6145, 110.9510),
    'MÄhia Peninsula, New Zealand': (-39.2610, 177.8640),
    'Semnan Space Center, Iran': (35.2340, 53.9210),
    'M?hia Peninsula, New Zealand': (-39.2610, 177.8640),
    'Vostochny Cosmodrome, Russia': (51.8840, 128.3330),
    'Palmachim Airbase, Israel': (31.8960, 34.6900),
    'Yasny Cosmodrome, Russia': (51.2070, 59.8500),
    'San Marco Launch Platform, Kenya': (-2.9360, 40.2120),
    'Marshall Islands, USA': (9.0450, 167.4600),
    'Alaska, USA': (57.4360, -152.3380),
    'RAAF Woomera Range Complex, Australia': (-31.1560, 136.8170),
    'Naro Space Center, South Korea': (34.4320, 127.5350),
    'Svobodny Cosmodrome, Russia': (51.7070, 128.0090),
    'Algeria, France': (30.2350, 3.1500),
    'Spaceport America, New Mexico': (32.9900, -106.9750),
    'New Mexico, USA': (32.9900, -106.9750),
    'Barents Sea Launch Area, Barents Sea': (71.0000, 28.0000),
    'Sohae Satellite Launching Station, North Korea': (39.6600, 124.7050),
    'Maranhão, Brazil': (-2.3160, -44.3840),
    'Tonghae Satellite Launching Ground, North Korea': (40.8550, 129.6640),
    'Tai Rui Barge, Yellow Sea': (35.0000, 123.0000),
    'Base Aerea de Gando, Gran Canaria': (27.9319, -15.3866),
    'Shahrud Missile Test Site, Iran': (36.2000, 55.2000),
    'Kauai, Pacific Missile Range Facility': (22.0220, -159.7850),
    'Launch Plateform, Shahrud Missile Test Site': (36.2000, 55.2000),
    'DeBo 3 Barge, Yellow Sea': (35.0000, 123.0000),
}

df = pd.read_csv(DATA)
df['Site'] = df['Location'].str.split(',').str[-2:].str.join(',').str.strip()

# 按发射场、时代、阵营统计
grouped = df.groupby(['Site', 'Era', 'Bloc']).size().reset_index(name='count')

records = []
for _, row in grouped.iterrows():
    site = row['Site']
    if site in site_coords:
        lat, lng = site_coords[site]
        records.append({
            'site': site,
            'era': row['Era'],
            'bloc': row['Bloc'],
            'count': int(row['count']),
            'lat': lat,
            'lng': lng,
        })

# 按发射场汇总总数
total = df.groupby('Site').size().reset_index(name='total')
site_totals = {}
for _, row in total.iterrows():
    if row['Site'] in site_coords:
        lat, lng = site_coords[row['Site']]
        site_totals[row['Site']] = {
            'lat': lat, 'lng': lng, 'total': int(row['total'])
        }

output = {
    'records': records,
    'sites': site_totals,
    'eras': ['Cold War', 'Post-Cold War', 'Early Commercial', 'New Space'],
    'blocs': ['Soviet/Russia', 'US Government', 'US Commercial', 'China', 'Joint Venture', 'Other'],
}

with open(ROOT / "globe" / "launch_data.json", 'w') as f:
    json.dump(output, f)

print("JSON生成完成")
print(f"总记录数: {len(records)}")