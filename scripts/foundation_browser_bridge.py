"""Browser-test transport to the real Flask request handlers; test DB supplied by parent."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'services/api'))
from growth import create_app

data = json.load(sys.stdin)
with create_app().test_client() as client:
    response = client.open(data['path'], method=data['method'], headers=data.get('headers', {}),
                           json=data.get('data'))
    print(json.dumps({'status': response.status_code, 'body': response.get_data(as_text=True)}))
