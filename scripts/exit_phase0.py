"""Local acceptance runner, not live-provider or production certification."""
import json
import os
import subprocess
import sys
import time
import uuid
from pathlib import Path

root=Path(__file__).resolve().parents[1]
os.chdir(root)
output=root/'artifacts/phase0-exit';output.mkdir(parents=True,exist_ok=True)
python=str(root/'.venv/Scripts/python.exe') if (root/'.venv/Scripts/python.exe').exists() else sys.executable
npm='npm.cmd' if os.name=='nt' else 'npm'
checks=[
 ('catalogue',[python,'scripts/validate_catalogue.py'],root),
 ('api-tests',[python,'-m','pytest','-q','--cov=growth','--cov-fail-under=85',
               '--basetemp='+str(output/('pytest-'+uuid.uuid4().hex))],root/'services/api'),
 ('api-lint',[python,'-m','ruff','check','growth','tests'],root/'services/api'),
 ('frontend-build',[npm,'run','build'],root/'frontend'),
 ('browser',[python,'scripts/run_foundation_browser.py'],root),
 ('offline',['node','scripts/test_offline_shell.cjs'],root),
 ('stack',['docker','compose','exec','-T','api','python','check_stack.py'],root),
 ('storage',['docker','compose','exec','-T','api','python','check_storage.py'],root),
 ('restore',[python,'scripts/check_restore.py'],root),
 ('worker-restart',[python,'scripts/check_worker_restart.py'],root),
 ('load',['docker','compose','exec','-T','api','python','check_load.py'],root),
]
results=[]
for name,command,cwd in checks:
    start=time.monotonic()
    with (output/(name+'.log')).open('wb') as log:
        code=subprocess.run(command,cwd=cwd,stdout=log,stderr=subprocess.STDOUT).returncode
    results.append({'check':name,'passed':code==0,'seconds':round(time.monotonic()-start,2)})
    print(name+': '+('PASS' if code==0 else 'FAIL'),flush=True)
    if code:break
report={'local_acceptance':all(row['passed'] for row in results) and len(results)==len(checks),
        'checks':results,'provider_sandbox':'not_verified','human_language_review':'not_verified',
        'production_certification':False}
(output/'report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
sys.exit(0 if report['local_acceptance'] else 1)
