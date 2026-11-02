import sqlite3
import tempfile
import unittest
import json
from pathlib import Path
import server
from server import Handler, Problem, connect, init_db, service


class WorkflowTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.db = Path(self.temp.name) / 'test.sqlite3'
        init_db(self.db)

    def tearDown(self):
        self.temp.cleanup()

    def call(self, method, path, data=None, workspace='demo-a'):
        return service(method, path, data, workspace, self.db)

    def published(self):
        post = self.call('POST', '/api/posts', {'caption': 'A real idea'})
        self.call('POST', f"/api/posts/{post['id']}/approve")
        return self.call('POST', f"/api/posts/{post['id']}/publish")

    def test_full_workflow_and_refund(self):
        post = self.published()
        lead = self.call('POST', '/api/leads', {'name': 'Customer', 'post_id': post['id']})
        request = {'post_id': post['id'], 'lead_id': lead['id'], 'amount_paise': 125000, 'idempotency_key': 'sale-1'}
        sale = self.call('POST', '/api/sales', request)
        self.assertEqual(sale, self.call('POST', '/api/sales', request))
        state = self.call('GET', '/api/state')
        self.assertEqual(state['dashboard'], {'revenue_paise': 125000, 'sales_count': 1, 'leads_count': 1, 'published_count': 1})
        path = f"/api/sales/{sale['id']}/refund"
        refund = self.call('POST', path, {'idempotency_key': 'refund-1'})
        self.assertEqual(refund, self.call('POST', path, {'idempotency_key': 'refund-1'}))
        state = self.call('GET', '/api/state')
        self.assertEqual(state['dashboard']['revenue_paise'], 0)
        self.assertEqual(len(state['ledger']), 2)
        self.assertEqual(len(state['audit']), 6)
        with self.assertRaises(Problem):
            self.call('POST', path, {'idempotency_key': 'refund-2'})

    def test_isolation_on_reads_and_related_writes(self):
        post = self.published()
        lead = self.call('POST', '/api/leads', {'name': 'A'})
        sale = self.call('POST', '/api/sales', {'post_id': post['id'], 'amount_paise': 100, 'idempotency_key': 's'})
        state = self.call('GET', '/api/state', workspace='demo-b')
        for key in ['posts', 'leads', 'sales', 'audit', 'ledger']:
            self.assertEqual(state[key], [])
        for path, data in [(f"/api/posts/{post['id']}/approve", {}), ('/api/leads', {'name': 'B', 'post_id': post['id']}),
                           ('/api/sales', {'post_id': post['id'], 'amount_paise': 100, 'idempotency_key': 'x'}),
                           (f"/api/sales/{sale['id']}/refund", {'idempotency_key': 'r'})]:
            with self.assertRaises(Problem) as caught:
                self.call('POST', path, data, 'demo-b')
            self.assertEqual(caught.exception.status, 404)
        bpost = self.call('POST', '/api/posts', {'caption': 'B'}, 'demo-b')
        self.call('POST', f"/api/posts/{bpost['id']}/approve", workspace='demo-b')
        self.call('POST', f"/api/posts/{bpost['id']}/publish", workspace='demo-b')
        with self.assertRaises(Problem):
            self.call('POST', '/api/sales', {'post_id': bpost['id'], 'lead_id': lead['id'], 'amount_paise': 100, 'idempotency_key': 'b'}, 'demo-b')

    def test_invalid_state_and_fields(self):
        for caption in ['', 'x' * 2201, 42, None]:
            with self.assertRaises(Problem):
                self.call('POST', '/api/posts', {'caption': caption})
        post = self.call('POST', '/api/posts', {'caption': 'draft'})
        with self.assertRaises(Problem):
            self.call('POST', f"/api/posts/{post['id']}/publish")
        for amount in [0, -1, 1.5, True, '100', 100_000_001]:
            with self.assertRaises(Problem):
                self.call('POST', '/api/sales', {'post_id': post['id'], 'amount_paise': amount, 'idempotency_key': 'a'})
        with self.assertRaises(Problem):
            self.call('GET', '/api/state', workspace='arbitrary')
        with self.assertRaises(Problem):
            self.call('POST', '/api/posts', [])

    def test_idempotency_conflict_and_atomicity(self):
        post = self.published()
        request = {'post_id': post['id'], 'amount_paise': 100, 'idempotency_key': 'unique'}
        self.call('POST', '/api/sales', request)
        with self.assertRaises(Problem) as caught:
            self.call('POST', '/api/sales', {**request, 'amount_paise': 200})
        self.assertEqual(caught.exception.status, 409)
        self.assertEqual(len(self.call('GET', '/api/state')['ledger']), 1)

    def test_ledger_and_audit_immutable(self):
        post = self.published()
        self.call('POST', '/api/sales', {'post_id': post['id'], 'amount_paise': 100, 'idempotency_key': 's'})
        for sql in ['UPDATE ledger SET amount_paise=500', 'DELETE FROM ledger', 'DELETE FROM audit', "UPDATE audit SET action='changed'"]:
            with connect(self.db) as db:
                with self.assertRaises(sqlite3.IntegrityError):
                    db.execute(sql)

    def test_http_transport_and_cross_site_rejection(self):
        import io
        original_service = server.service
        server.service = lambda method, path, data, workspace: original_service(method, path, data, workspace, self.db)

        class Socket:
            def __init__(self, request):
                self.input = io.BytesIO(request)
                self.output = io.BytesIO()
            def makefile(self, *args):
                return self.input
            def sendall(self, data):
                self.output.write(data)

        def request(method, path, body='', origin='http://localhost:5173', workspace='demo-a'):
            encoded = body.encode()
            raw = (f'{method} {path} HTTP/1.0\r\nHost: localhost:8000\r\n'
                   f'Content-Type: application/json\r\nOrigin: {origin}\r\n'
                   f'X-Workspace-ID: {workspace}\r\nContent-Length: {len(encoded)}\r\n\r\n').encode() + encoded
            connection = Socket(raw)
            Handler(connection, ('127.0.0.1', 12345), None)
            head, payload = connection.output.getvalue().split(b'\r\n\r\n', 1)
            return head.decode(), json.loads(payload)
        try:
            head, result = request('POST', '/api/posts', json.dumps({'caption': 'HTTP draft'}))
            self.assertIn('200 OK', head)
            self.assertIn('Access-Control-Allow-Origin: http://localhost:5173', head)
            self.assertEqual(result['status'], 'draft')
            _, state = request('GET', '/api/state', workspace='demo-b')
            self.assertEqual(state['posts'], [])
            head, result = request('POST', '/api/posts', '{')
            self.assertIn('400 Bad Request', head)
            self.assertEqual(result['error']['code'], 'invalid_json')
            head, result = request('POST', '/api/posts', json.dumps({'caption': 'hostile'}), origin='https://example.com')
            self.assertIn('403 Forbidden', head)
            self.assertEqual(len(self.call('GET', '/api/state')['posts']), 1)
        finally:
            server.service = original_service

    def test_static_allowlist_blocks_source_and_path_traversal(self):
        import io

        class Socket:
            def __init__(self, path):
                self.input = io.BytesIO(f'GET {path} HTTP/1.0\r\nHost: localhost:8000\r\n\r\n'.encode())
                self.output = io.BytesIO()
            def makefile(self, *args):
                return self.input
            def sendall(self, data):
                self.output.write(data)

        original_root = server.WEB_ROOT
        web = Path(self.temp.name) / 'web'
        web.mkdir()
        (web / 'index.html').write_text('<h1>Demo</h1>')
        (web / 'app.js').write_text('const demo = true;')
        (web / 'styles.css').write_text('body {color: black}')
        (web / 'private.txt').write_text('must not be exposed')
        server.WEB_ROOT = web
        try:
            for path in ['/', '/index.html', '/app.js?v=1', '/styles.css']:
                connection = Socket(path)
                Handler(connection, ('127.0.0.1', 12345), None)
                output = connection.output.getvalue()
                self.assertIn(b'200 OK', output)
                self.assertIn(b'X-Content-Type-Options: nosniff', output)
            for path in ['/../backend/server.py', '/%2e%2e/backend/server.py', '/docs/features.csv',
                         '/backend/demo.sqlite3', '/private.txt', '/app.js/../private.txt', '/web/index.html']:
                connection = Socket(path)
                Handler(connection, ('127.0.0.1', 12345), None)
                output = connection.output.getvalue()
                self.assertIn(b'404 Not Found', output, path)
                self.assertNotIn(b'must not be exposed', output)
        finally:
            server.WEB_ROOT = original_root


if __name__ == '__main__':
    unittest.main()
