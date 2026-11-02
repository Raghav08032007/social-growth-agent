"""Temporary SQLite + actual Flask handlers behind Playwright interception; no live HTTP claim."""
import base64
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

root = Path(__file__).resolve().parents[1]
os.chdir(root)
sys.path.insert(0, str(root / 'services/api'))
with tempfile.TemporaryDirectory() as directory:
    os.environ.update(DATABASE_URL='sqlite:///' + (Path(directory)/'browser.sqlite3').as_posix(),
        REDIS_URL='redis://localhost:6379/0', APP_ENV='testing', VAULT_ACTIVE_KEY='test',
        VAULT_KEYS=json.dumps({'test':base64.urlsafe_b64encode(os.urandom(32)).decode()}))
    from alembic import command
    from alembic.config import Config
    config = Config(str(root/'services/api/alembic.ini'))
    config.set_main_option('script_location', str(root/'services/api/migrations'))
    command.upgrade(config, 'head')
    from growth import create_app
    from growth.costs import record_cost
    from growth.db import transaction
    from growth.models import Job, Membership, User, Workspace
    from growth.security import issue_session
    app=create_app()
    with transaction(app.extensions['engine']) as db:
        user,workspace=User(name='Fixture staff',is_staff=True),Workspace(name='Foundation test')
        db.add_all([user,workspace]);db.flush()
        db.add(Membership(user_id=user.id,workspace_id=workspace.id,role='owner'))
        os.environ['FOUNDATION_SESSION']=issue_session(db,user.id)
        record_cost(db,workspace.id,'browser-fixture',50000)
        db.add(Job(workspace_id=workspace.id,idempotency_key='browser-fixture',
                   kind='diagnostic.retry',payload={'fail_until':0},status='succeeded'))
    os.environ['FOUNDATION_PYTHON']=sys.executable
    (root/'artifacts').mkdir(exist_ok=True)
    result=subprocess.run(['node','scripts/foundation_browser.cjs'],check=False)
    app.extensions['engine'].dispose()
    sys.exit(result.returncode)
