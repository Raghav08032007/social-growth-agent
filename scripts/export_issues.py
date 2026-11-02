"""Export a reviewable backlog. Does not create remote issues."""
import csv
import json
from pathlib import Path

root = Path(__file__).resolve().parents[1]
rows = list(csv.DictReader((root / 'docs/features.csv').open(encoding='utf-8-sig', newline='')))
issues = [{
    'title': f"P{r['phase']} {r['feature_id']}: {r['feature_name']}",
    'labels': [f"phase:{r['phase']}", f"family:{r['feature_id'].split('-')[0]}", 'planned'],
    'body': f"Original source feature: {r['feature_id']}. Status: planned.\n\nRefine before implementation: user story, role, data ownership, states, API, jobs, provider evidence, UI/error states, tests, cost cap and runbook. See docs/FEATURE_GUIDE.md and docs/verification.md.\n\nAcceptance criteria and provider evidence: not specified yet. Do not mark complete based on this issue template.",
} for r in rows]
out = root / 'artifacts'
out.mkdir(exist_ok=True)
(out / 'github-issues.json').write_text(json.dumps(issues, indent=2, ensure_ascii=False), encoding='utf-8')
print(f'Exported {len(issues)} planned issue drafts to artifacts/github-issues.json; no remote changes.')
