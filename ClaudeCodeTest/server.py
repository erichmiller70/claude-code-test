"""
Local dev server that serves static files and proxies /api/chat to n8n.
This avoids CORS issues when calling n8n from localhost.

Usage: python server.py
Then open http://localhost:8080
"""

import http.server
import json
import os
import urllib.request
import urllib.error
import urllib.parse

# Load .env file for local development
env_path = os.path.join(os.path.dirname(__file__), '.env')
if os.path.exists(env_path):
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, val = line.split('=', 1)
                os.environ.setdefault(key.strip(), val.strip())

N8N_WEBHOOK_URL = os.environ.get('N8N_WEBHOOK_URL', '')
PORT = 8080


class ProxyHandler(http.server.SimpleHTTPRequestHandler):
    def do_POST(self):
        print(f'[POST] {self.path}')

        if self.path.startswith('/api/chat'):
            content_length = int(self.headers.get('Content-Length', 0))
            body = json.loads(self.rfile.read(content_length))

            # Forward as GET with query parameters (n8n webhook is set to GET)
            params = urllib.parse.urlencode({
                'chatInput': body.get('chatInput', ''),
                'sessionId': body.get('sessionId', '')
            })
            url = f'{N8N_WEBHOOK_URL}?{params}'
            print(f'[PROXY] GET {url}')

            req = urllib.request.Request(url, method='GET')

            try:
                with urllib.request.urlopen(req) as resp:
                    resp_body = resp.read()
                    content_type = resp.getheader('Content-Type', 'text/plain')
                    print(f'[PROXY] n8n responded {resp.status} ({content_type}): {resp_body[:200]}')

                    # Normalize n8n response to { "output": "..." }
                    try:
                        data = json.loads(resp_body)
                        # n8n returns [{"text": "..."}] — extract the text
                        if isinstance(data, list) and len(data) > 0:
                            data = data[0]
                        text = data.get('text') or data.get('output') or data.get('reply') or json.dumps(data)
                    except (json.JSONDecodeError, AttributeError):
                        text = resp_body.decode('utf-8', errors='replace')

                    normalized = json.dumps({'output': text}).encode()
                    self.send_response(resp.status)
                    self.send_header('Content-Type', 'application/json')
                    self.end_headers()
                    self.wfile.write(normalized)
            except urllib.error.HTTPError as e:
                error_body = e.read()
                print(f'[PROXY] n8n error {e.code}: {error_body[:200]}')
                self.send_response(e.code)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(error_body)
            except Exception as e:
                print(f'[PROXY] Exception: {e}')
                self.send_response(502)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'error': str(e)}).encode())
        else:
            self.send_response(404)
            self.send_header('Content-Type', 'text/plain')
            self.end_headers()
            self.wfile.write(b'Not found')


if __name__ == '__main__':
    with http.server.HTTPServer(('', PORT), ProxyHandler) as httpd:
        print(f'Serving on http://localhost:{PORT}')
        print(f'Proxying /api/chat -> {N8N_WEBHOOK_URL}')
        httpd.serve_forever()
