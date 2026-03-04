from http.server import BaseHTTPRequestHandler
import json
import os
import urllib.request
import urllib.error
import urllib.parse


class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        webhook_url = os.environ.get('N8N_WEBHOOK_URL', '')
        if not webhook_url:
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'error': 'N8N_WEBHOOK_URL not configured'}).encode())
            return

        content_length = int(self.headers.get('Content-Length', 0))
        body = json.loads(self.rfile.read(content_length))

        # Forward as GET with query parameters (n8n webhook is set to GET)
        params = urllib.parse.urlencode({
            'chatInput': body.get('chatInput', ''),
            'sessionId': body.get('sessionId', '')
        })
        url = f'{webhook_url}?{params}'

        req = urllib.request.Request(url, method='GET')

        try:
            with urllib.request.urlopen(req) as resp:
                resp_body = resp.read()

                # Normalize n8n response to { "output": "..." }
                try:
                    data = json.loads(resp_body)
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
            self.send_response(e.code)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(error_body)
        except Exception as e:
            self.send_response(502)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'error': str(e)}).encode())
