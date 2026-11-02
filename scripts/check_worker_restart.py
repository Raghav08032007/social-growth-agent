"""Development-only worker restart drill. Always attempts to bring the worker back."""
import json
import subprocess
import time


def run(args,body=None):
    result=subprocess.run(['docker','compose',*args],input=body,capture_output=True)
    if result.returncode:
        raise RuntimeError('Worker recovery diagnostic command failed')
    return result.stdout


bootstrap=b'''
import json,uuid
from growth import create_app
from growth.db import transaction
from growth.jobs import enqueue
from growth.models import Workspace
app=create_app()
with transaction(app.extensions['engine']) as db:
    w=Workspace(name='Worker restart '+uuid.uuid4().hex[:8]);db.add(w);db.flush()
    job=enqueue(db,w.id,uuid.uuid4().hex,'diagnostic.retry',{'fail_until':0})
    print(json.dumps({'workspace':w.id,'job':job.id,'status':job.status}))
'''
stopped=False
try:
    run(['stop','worker']);stopped=True
    fixture=json.loads(run(['exec','-T','api','python','-'],bootstrap))
    assert fixture['status']=='queued'
finally:
    if stopped:run(['up','-d','--no-deps','worker'])

query=f'''
import json
from growth import create_app
from growth.db import transaction
from growth.models import Job
app=create_app()
with transaction(app.extensions['engine']) as db:
    row=db.get(Job,{fixture['job']!r})
    print(json.dumps({{'status':row.status,'attempts':row.attempts}}))
'''.encode()
deadline=time.monotonic()+60
while time.monotonic()<deadline:
    result=json.loads(run(['exec','-T','api','python','-'],query))
    if result=={'status':'succeeded','attempts':1}:break
    time.sleep(1)
else:raise AssertionError('Queued job did not recover after worker restart')
print(json.dumps({'worker_restart':'passed','durable_job':'succeeded','attempts':1}))
