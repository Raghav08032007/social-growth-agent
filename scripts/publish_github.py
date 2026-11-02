"""Create a public repository using existing Git Credential Manager auth; never print credentials.

Run deliberately after reviewing the commit. Existing remote repositories are not modified.
"""
import json
import os
import subprocess
import urllib.error
import urllib.request

env = dict(os.environ, GIT_TERMINAL_PROMPT='0', GCM_INTERACTIVE='Never')
credential = subprocess.run(['git', 'credential', 'fill'], input='protocol=https\nhost=github.com\n\n',
                            text=True, capture_output=True, env=env)
if credential.returncode:
    raise SystemExit('GitHub authentication unavailable. Authenticate Git Credential Manager first.')
fields = dict(line.split('=', 1) for line in credential.stdout.splitlines() if '=' in line)
token = fields.get('password')
if not token:
    raise SystemExit('GitHub credential did not supply a token.')

def api(method, path, payload=None):
    request = urllib.request.Request('https://api.github.com' + path, method=method,
        data=None if payload is None else json.dumps(payload).encode(),
        headers={'Authorization': 'Bearer ' + token, 'Accept': 'application/vnd.github+json',
                 'X-GitHub-Api-Version': '2022-11-28', 'User-Agent': 'social-growth-agent-publisher'})
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)

try:
    user = api('GET', '/user')
    owner = user['login']
    name = 'social-growth-agent'
    try:
        api('GET', f'/repos/{owner}/{name}')
    except urllib.error.HTTPError as exc:
        if exc.code != 404:
            raise
    else:
        raise SystemExit(f'Repository {owner}/{name} already exists; no remote changes made.')
    repo = api('POST', '/user/repos', {'name': name, 'private': False,
        'description': 'India-focused social-to-revenue SaaS planning package and local reference demo. Production integrations remain planned.',
        'auto_init': False})
    print('Created public repository:', repo['html_url'])
    subprocess.run(['git', 'remote', 'add', 'origin', repo['clone_url']], check=True)
    subprocess.run(['git', 'push', '-u', 'origin', 'main'], check=True, env=env)
    print('Published:', repo['html_url'])
except urllib.error.HTTPError as exc:
    raise SystemExit(f'GitHub API returned HTTP {exc.code}; no credentials printed.')
