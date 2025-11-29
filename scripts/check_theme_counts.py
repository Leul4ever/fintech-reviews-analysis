#!/usr/bin/env python
"""Quick script to check theme counts per bank."""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import pandas as pd

df = pd.read_csv('data/processed/theme_summary.csv')
print('Theme counts per bank:')
print('=' * 60)
for bank in df['bank'].unique():
    subset = df[df['bank'] == bank]
    count = len(subset)
    themes = subset['theme'].tolist()
    print(f'\n{bank}:')
    print(f'  Total themes: {count}')
    print(f'  Themes: {", ".join(themes)}')
    print(f'  Coverage: {subset["coverage_pct"].sum():.1f}%')

print('\n' + '=' * 60)
print('✅ All banks have 3+ themes!' if all(len(df[df['bank']==bank]) >= 3 for bank in df['bank'].unique()) else '⚠️ Some banks have <3 themes')

