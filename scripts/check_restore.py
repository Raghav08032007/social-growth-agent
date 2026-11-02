"""Disposable MySQL backup/restore drill; SQL stays in memory, secrets are never printed."""
import hashlib
import json
import re
import subprocess
import uuid


def run(arguments,input=None):
    result=subprocess.run(['docker','compose',*arguments],input=input,capture_output=True)
    if result.returncode:
        raise RuntimeError('Restore diagnostic subprocess failed; no dump or credentials printed')
    return result.stdout


bootstrap=b'''
import json,uuid
from growth import create_app
from growth.db import transaction
from growth.models import Workspace,timestamp
from growth.jobs import enqueue
app=create_app()
with transaction(app.extensions['engine']) as db:
    w=Workspace(name='Recovery diagnostic '+uuid.uuid4().hex[:8]);db.add(w);db.flush()
    token=app.extensions['vault'].store(db,w.id,'diagnostic',uuid.uuid4().hex,'recovery-fixture-not-a-real-token',[])
    job=enqueue(db,w.id,uuid.uuid4().hex,'diagnostic.retry',{'fail_until':0});job.available_at=timestamp()+86400
    print(json.dumps({'workspace':w.id,'token':token,'job':job.id}))
'''
fixture=json.loads(run(['exec','-T','api','python','-'],bootstrap))
name='growth_restore_'+uuid.uuid4().hex
assert re.fullmatch(r'growth_restore_[0-9a-f]{32}',name)
created=False
try:
    dump=run(['exec','-T','mysql','sh','-c',
        'MYSQL_PWD="$MYSQL_ROOT_PASSWORD" mysqldump -uroot --single-transaction --skip-lock-tables --no-tablespaces growth'])
    run(['exec','-T','mysql','sh','-c','MYSQL_PWD="$MYSQL_ROOT_PASSWORD" mysql -uroot'],
        f'CREATE DATABASE `{name}`;'.encode())
    created=True
    run(['exec','-T','mysql','sh','-c',f'MYSQL_PWD="$MYSQL_ROOT_PASSWORD" mysql -uroot {name}'],dump)
    result=run(['run','--rm','--no-deps','migrate','python','check_recovery.py',name,
                fixture['workspace'],fixture['token'],fixture['job']])
    print(result.decode().strip())
    print(json.dumps({'dump_bytes':len(dump),'sha256':hashlib.sha256(dump).hexdigest(),
                      'plaintext_dump_written':False}))
finally:
    if created:
        # Only this invocation's freshly created, exact-prefix UUID schema is removed.
        run(['exec','-T','mysql','sh','-c','MYSQL_PWD="$MYSQL_ROOT_PASSWORD" mysql -uroot'],
            f'DROP DATABASE `{name}`;'.encode())
    cleanup=f'''
from growth import create_app
from growth.db import transaction
from growth.models import Job
app=create_app()
with transaction(app.extensions['engine']) as db:
    app.extensions['vault'].revoke(db,{fixture['workspace']!r},{fixture['token']!r},'recovery-diagnostic')
    row=db.get(Job,{fixture['job']!r});row.status='cancelled';row.last_error='recovery_diagnostic_complete'
'''
    run(['exec','-T','api','python','-'],cleanup.encode())
