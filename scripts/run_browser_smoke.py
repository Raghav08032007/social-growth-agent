"""Self-contained server/browser check using a temporary database; no live providers."""
import os
import subprocess
import sys
import tempfile
import threading
from pathlib import Path

root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root))
os.chdir(root)
with tempfile.TemporaryDirectory() as folder:
    os.environ['DEMO_DB_PATH'] = str(Path(folder) / 'browser.sqlite3')
    from backend.server import Handler, ThreadingHTTPServer, init_db
    init_db()
    server = ThreadingHTTPServer(('127.0.0.1', 8000), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        result = subprocess.run(['node', 'scripts/browser_smoke.cjs'], check=False)
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)
    sys.exit(result.returncode)
