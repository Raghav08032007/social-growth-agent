"""Create ignored development environment secrets once. Existing .env is never replaced."""
import base64
import os
import secrets
from pathlib import Path

root = Path(__file__).resolve().parents[1]
path = root / '.env'
try:
    with path.open('x', encoding='utf-8') as file:
        file.write('MYSQL_PASSWORD=' + secrets.token_hex(24) + '\n')
        file.write('MYSQL_ROOT_PASSWORD=' + secrets.token_hex(24) + '\n')
        key = base64.urlsafe_b64encode(os.urandom(32)).decode()
        file.write('VAULT_KEYS=\'{"local-v1":"' + key + '"}\'\n')
except FileExistsError:
    print('.env already exists; preserving current credentials.')
else:
    print('Created ignored .env with random local secrets. Back up vault keys securely.')

# Add newly required local-only storage credentials without replacing existing keys.
existing = path.read_text(encoding='utf-8')
with path.open('a',encoding='utf-8') as file:
    for name in ('S3_ACCESS_KEY','S3_SECRET_KEY'):
        if not any(line.startswith(name+'=') for line in existing.splitlines()):
            file.write(name+'='+secrets.token_hex(24)+'\n')
