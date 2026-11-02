"""Validate preserved source inventory; no network or dependencies."""
import csv
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
rows = list(csv.DictReader((ROOT / 'docs/features.csv').open(encoding='utf-8-sig', newline='')))
expected = {0: 4, 1: 34, 2: 13, 3: 21, 4: 10, 5: 36, 6: 37, 7: 20, 8: 23, 9: 29, 10: 30}
assert len(rows) == 257, f'Expected 257 rows, got {len(rows)}'
assert len({r['feature_id'] for r in rows}) == 257, 'Duplicate feature ID'
assert Counter(int(r['phase']) for r in rows) == expected, 'Phase count mismatch'
assert all(r['feature_name'].strip() and r['status'] == 'planned' for r in rows)
assert sum(int(r['phase']) <= 4 for r in rows) == 82
print('PASS: 257 unique planned features; 11 phase totals match; P0–P4 = 82.')
