# -*- coding: utf-8 -*-
"""Inspect NAV_ITEMS from app.py."""
import sys
sys.stdout.reconfigure(encoding='utf-8')

code = open('app.py', encoding='utf-8').read()
lines = code.split('\n')

# Find NAV_ITEMS definition
for i, l in enumerate(lines):
    if 'NAV_ITEMS' in l and ('=' in l or '[' in l):
        for j in range(i, i+20):
            clean = lines[j].encode('ascii', 'replace').decode('ascii')
            print(j+1, ':', clean[:180])
            if ']' in lines[j] and j > i:
                break
        break
