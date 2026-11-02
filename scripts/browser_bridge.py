"""Test-only Playwright transport bridge to the actual backend service."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from backend.server import Problem, service

request = json.load(sys.stdin)
try:
    value = service(request['method'], request['path'], request.get('data'))
    print(json.dumps({'status': 200, 'body': value}))
except Problem as exc:
    print(json.dumps({'status': exc.status, 'body': {'error': {'code': exc.code, 'message': exc.message}}}))
