"""Local-only reference workflow. No real accounts, messages, publishing or money."""
import json
import os
import re
import sqlite3
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

DB_PATH = Path(os.environ.get('DEMO_DB_PATH', Path(__file__).with_name('demo.sqlite3')))
WORKSPACES = {'demo-a', 'demo-b'}
WEB_ROOT = Path(__file__).resolve().parent.parent / 'web'
STATIC_FILES = {'/': ('index.html', 'text/html; charset=utf-8'),
                '/index.html': ('index.html', 'text/html; charset=utf-8'),
                '/app.js': ('app.js', 'text/javascript; charset=utf-8'),
                '/styles.css': ('styles.css', 'text/css; charset=utf-8')}


class Connection(sqlite3.Connection):
    def __exit__(self, *args):
        try:
            return super().__exit__(*args)
        finally:
            self.close()


class Problem(Exception):
    def __init__(self, code, message, status=400):
        self.code, self.message, self.status = code, message, status


def connect(path=DB_PATH):
    db = sqlite3.connect(path, timeout=10, factory=Connection)
    db.row_factory = sqlite3.Row
    db.execute('PRAGMA foreign_keys=ON')
    return db


def init_db(path=DB_PATH):
    with connect(path) as db:
        db.executescript('''
        CREATE TABLE IF NOT EXISTS posts(id INTEGER PRIMARY KEY, workspace TEXT NOT NULL,
          caption TEXT NOT NULL, platform TEXT NOT NULL, language TEXT NOT NULL, status TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS leads(id INTEGER PRIMARY KEY, workspace TEXT NOT NULL,
          name TEXT NOT NULL, phone TEXT NOT NULL, post_id INTEGER REFERENCES posts(id), stage TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS sales(id INTEGER PRIMARY KEY, workspace TEXT NOT NULL,
          post_id INTEGER NOT NULL REFERENCES posts(id), lead_id INTEGER REFERENCES leads(id),
          amount_paise INTEGER NOT NULL CHECK(amount_paise>0), status TEXT NOT NULL,
          idempotency_key TEXT NOT NULL, UNIQUE(workspace,idempotency_key));
        CREATE TABLE IF NOT EXISTS operations(workspace TEXT NOT NULL, key TEXT NOT NULL,
          operation TEXT NOT NULL, payload TEXT NOT NULL, response TEXT NOT NULL,
          PRIMARY KEY(workspace,key));
        CREATE TABLE IF NOT EXISTS ledger(id INTEGER PRIMARY KEY, workspace TEXT NOT NULL,
          sale_id INTEGER NOT NULL REFERENCES sales(id), post_id INTEGER NOT NULL REFERENCES posts(id),
          amount_paise INTEGER NOT NULL, kind TEXT NOT NULL, created_at TEXT NOT NULL,
          UNIQUE(workspace,sale_id,kind));
        CREATE TABLE IF NOT EXISTS audit(id INTEGER PRIMARY KEY, workspace TEXT NOT NULL,
          action TEXT NOT NULL, entity_id INTEGER NOT NULL, created_at TEXT NOT NULL);
        CREATE TRIGGER IF NOT EXISTS immutable_ledger_update BEFORE UPDATE ON ledger
          BEGIN SELECT RAISE(ABORT,'ledger is immutable'); END;
        CREATE TRIGGER IF NOT EXISTS immutable_ledger_delete BEFORE DELETE ON ledger
          BEGIN SELECT RAISE(ABORT,'ledger is immutable'); END;
        CREATE TRIGGER IF NOT EXISTS immutable_audit_update BEFORE UPDATE ON audit
          BEGIN SELECT RAISE(ABORT,'audit is immutable'); END;
        CREATE TRIGGER IF NOT EXISTS immutable_audit_delete BEFORE DELETE ON audit
          BEGIN SELECT RAISE(ABORT,'audit is immutable'); END;
        ''')


def now():
    return datetime.now(timezone.utc).isoformat()


def text_field(data, key, maximum, default=None):
    value = data.get(key, default)
    if not isinstance(value, str) or not value.strip() or len(value) > maximum:
        raise Problem('validation', f'{key} must be nonempty text, at most {maximum} characters')
    return value.strip()


def integer(value, name):
    if type(value) is not int or value <= 0:
        raise Problem('validation', f'{name} must be a positive integer')
    return value


def owned(db, table, ident, workspace):
    integer(ident, table + '_id')
    row = db.execute(f'SELECT * FROM {table} WHERE id=? AND workspace=?', (ident, workspace)).fetchone()
    if row is None:
        raise Problem('not_found', 'Record not found in this demo workspace', 404)
    return dict(row)


def log(db, workspace, action, entity):
    db.execute('INSERT INTO audit(workspace,action,entity_id,created_at) VALUES(?,?,?,?)',
               (workspace, action, entity, now()))


def service(method, path, data=None, workspace='demo-a', db_path=DB_PATH):
    if workspace not in WORKSPACES:
        raise Problem('workspace', 'Choose demo-a or demo-b', 403)
    data = {} if data is None else data
    if not isinstance(data, dict):
        raise Problem('validation', 'JSON body must be an object')
    with connect(db_path) as db:
        if method == 'GET' and path == '/api/state':
            result = {'mode': 'demo', 'workspace_id': workspace}
            for table in ('posts', 'leads', 'sales', 'ledger', 'audit'):
                result[table] = [dict(r) for r in db.execute(
                    f'SELECT * FROM {table} WHERE workspace=? ORDER BY id DESC', (workspace,))]
            result['dashboard'] = {
                'revenue_paise': sum(r['amount_paise'] for r in result['ledger']),
                'sales_count': sum(s['status'] == 'paid' for s in result['sales']),
                'leads_count': len(result['leads']),
                'published_count': sum(p['status'] == 'published' for p in result['posts'])}
            return result
        if method != 'POST':
            raise Problem('not_found', 'Route not found', 404)
        # One write transaction covers read checks, side effects, and idempotency storage.
        db.execute('BEGIN IMMEDIATE')
        if path == '/api/posts':
            caption = text_field(data, 'caption', 2200)
            platform = text_field(data, 'platform', 30, 'instagram')
            language = text_field(data, 'language', 10, 'en')
            if platform not in {'instagram', 'facebook'} or language not in {'en', 'ta', 'hi'}:
                raise Problem('validation', 'Supported demo platforms: instagram/facebook; languages: en/ta/hi')
            cur = db.execute('INSERT INTO posts(workspace,caption,platform,language,status) VALUES(?,?,?,?,?)',
                             (workspace, caption, platform, language, 'draft'))
            log(db, workspace, 'draft.created', cur.lastrowid)
            return owned(db, 'posts', cur.lastrowid, workspace)
        match = re.fullmatch(r'/api/posts/(\d+)/(approve|publish)', path)
        if match:
            ident, action = int(match[1]), match[2]
            post = owned(db, 'posts', ident, workspace)
            target = 'approved' if action == 'approve' else 'published'
            expected = 'draft' if action == 'approve' else 'approved'
            if post['status'] == target:
                return post
            if post['status'] != expected:
                raise Problem('state_conflict', f'{action} requires status {expected}', 409)
            db.execute('UPDATE posts SET status=? WHERE id=? AND workspace=?', (target, ident, workspace))
            log(db, workspace, 'post.' + ('approved' if action == 'approve' else 'simulated_publish'), ident)
            return owned(db, 'posts', ident, workspace)
        if path == '/api/leads':
            name = text_field(data, 'name', 120)
            phone = data.get('phone', '')
            if not isinstance(phone, str) or len(phone) > 40:
                raise Problem('validation', 'phone must be text, at most 40 characters')
            post_id = data.get('post_id')
            if post_id is not None:
                owned(db, 'posts', post_id, workspace)
            cur = db.execute('INSERT INTO leads(workspace,name,phone,post_id,stage) VALUES(?,?,?,?,?)',
                             (workspace, name, phone, post_id, 'new'))
            log(db, workspace, 'lead.created', cur.lastrowid)
            return owned(db, 'leads', cur.lastrowid, workspace)
        refund = re.fullmatch(r'/api/sales/(\d+)/refund', path)
        if path == '/api/sales' or refund:
            key = text_field(data, 'idempotency_key', 100)
            payload = json.dumps(data, sort_keys=True, separators=(',', ':'))
            previous = db.execute('SELECT * FROM operations WHERE workspace=? AND key=?', (workspace, key)).fetchone()
            if previous:
                if previous['operation'] != path or previous['payload'] != payload:
                    raise Problem('idempotency_conflict', 'This key was used for a different request', 409)
                return json.loads(previous['response'])
            if refund:
                sale = owned(db, 'sales', int(refund[1]), workspace)
                if sale['status'] != 'paid':
                    raise Problem('state_conflict', 'Sale already refunded', 409)
                db.execute('UPDATE sales SET status=? WHERE id=? AND workspace=?', ('refunded', sale['id'], workspace))
                amount, kind = -sale['amount_paise'], 'refund'
                sale['status'] = 'refunded'
            else:
                post_id = integer(data.get('post_id'), 'post_id')
                post = owned(db, 'posts', post_id, workspace)
                if post['status'] != 'published':
                    raise Problem('state_conflict', 'Sale requires a simulated published post', 409)
                amount = integer(data.get('amount_paise'), 'amount_paise')
                if amount > 100_000_000:
                    raise Problem('validation', 'Demo sale limit is Rs 10 lakh')
                lead_id = data.get('lead_id')
                if lead_id is not None:
                    lead = owned(db, 'leads', lead_id, workspace)
                    if lead['post_id'] not in (None, post_id):
                        raise Problem('validation', 'Lead belongs to a different post')
                cur = db.execute('INSERT INTO sales(workspace,post_id,lead_id,amount_paise,status,idempotency_key) VALUES(?,?,?,?,?,?)',
                                 (workspace, post_id, lead_id, amount, 'paid', key))
                sale = owned(db, 'sales', cur.lastrowid, workspace)
                kind = 'sale'
            db.execute('INSERT INTO ledger(workspace,sale_id,post_id,amount_paise,kind,created_at) VALUES(?,?,?,?,?,?)',
                       (workspace, sale['id'], sale['post_id'], amount, kind, now()))
            log(db, workspace, 'demo.' + kind, sale['id'])
            db.execute('INSERT INTO operations VALUES(?,?,?,?,?)', (workspace, key, path, payload, json.dumps(sale)))
            return sale
        raise Problem('not_found', 'Route not found', 404)


class Handler(BaseHTTPRequestHandler):
    def serve_static(self):
        # Exact URL allowlist: no source, docs, database, encoded paths or traversal.
        selected = STATIC_FILES.get(urlsplit(self.path).path)
        if selected is None:
            raise Problem('not_found', 'Page not found', 404)
        try:
            encoded = (WEB_ROOT / selected[0]).read_bytes()
        except OSError:
            raise Problem('not_found', 'Demo web file not available', 404)
        self.send_response(200)
        self.send_header('Content-Type', selected[1])
        self.send_header('Content-Length', str(len(encoded)))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.end_headers()
        self.wfile.write(encoded)

    def respond(self, status, body):
        encoded = json.dumps(body).encode()
        self.send_response(status)
        origin = self.headers.get('Origin')
        if origin in {'http://localhost:5173', 'http://127.0.0.1:5173'}:
            self.send_header('Access-Control-Allow-Origin', origin)
            self.send_header('Vary', 'Origin')
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(encoded)))
        self.send_header('Cache-Control', 'no-store')
        self.end_headers()
        self.wfile.write(encoded)

    def do_OPTIONS(self):
        self.send_response(204)
        if self.headers.get('Origin') in {'http://localhost:5173', 'http://127.0.0.1:5173'}:
            self.send_header('Access-Control-Allow-Origin', self.headers['Origin'])
            self.send_header('Access-Control-Allow-Headers', 'Content-Type, X-Workspace-ID')
            self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.end_headers()

    def handle_api(self):
        try:
            # Browser-origin guard: local demo has no authentication and must not accept cross-site writes.
            if self.headers.get('Host') not in {'localhost:8000', '127.0.0.1:8000'}:
                raise Problem('host', 'Use localhost:8000', 403)
            origin = self.headers.get('Origin')
            if origin and origin not in {'http://localhost:5173', 'http://127.0.0.1:5173',
                                         'http://localhost:8000', 'http://127.0.0.1:8000'}:
                raise Problem('origin', 'Unknown demo browser origin', 403)
            if self.command == 'GET' and not self.path.startswith('/api/'):
                self.serve_static()
                return
            data = None
            if self.command == 'POST':
                if self.headers.get('Content-Type', '').split(';')[0] != 'application/json':
                    raise Problem('content_type', 'Send application/json', 415)
                try:
                    length = int(self.headers.get('Content-Length', '0'))
                except ValueError:
                    raise Problem('validation', 'Invalid Content-Length')
                if length < 0 or length > 16384:
                    raise Problem('too_large', 'Request body limit is 16 KiB', 413)
                try:
                    data = json.loads(self.rfile.read(length) or b'{}')
                except (ValueError, UnicodeDecodeError):
                    raise Problem('invalid_json', 'Send valid JSON')
            result = service(self.command, self.path, data,
                             self.headers.get('X-Workspace-ID', 'demo-a'))
            self.respond(200, result)
        except Problem as exc:
            self.respond(exc.status, {'error': {'code': exc.code, 'message': exc.message}})
        except sqlite3.Error:
            self.respond(500, {'error': {'code': 'database', 'message': 'Local database operation failed'}})

    do_GET = handle_api
    do_POST = handle_api


if __name__ == '__main__':
    init_db()
    print('DEMO ONLY: http://127.0.0.1:8000 — simulated publishing and money; no authentication')
    ThreadingHTTPServer(('127.0.0.1', 8000), Handler).serve_forever()
