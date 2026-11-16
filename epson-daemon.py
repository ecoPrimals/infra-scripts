#!/usr/bin/env python3
"""epson-daemon.py — Gaia's Epson nerve endpoints
Runs on port 8084, callable from any gate on the mesh.

GET  /scan?tag=xxx         — trigger ADF scan, returns manifest
GET  /print?file=path      — print a file
POST /print                — print POST body as text
GET  /status               — scanner + printer status
GET  /scans                — list all scan batches
"""
import http.server
import json
import subprocess
import os
import glob
from urllib.parse import urlparse, parse_qs
from datetime import datetime

PORT = 8084
SCRIPT_DIR = "/home/eastgate/Development/ecoPrimals/infra/scripts"
SCAN_DIR = "/home/eastgate/Development/ecoPrimals/data/body/scans"
PRINT_DIR = "/home/eastgate/Development/ecoPrimals/data/body/prints"

class EpsonHandler(http.server.BaseHTTPRequestHandler):
    def _json(self, code, data):
        self.send_response(code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data, indent=2).encode())

    def do_GET(self):
        url = urlparse(self.path)
        params = parse_qs(url.query)

        if url.path == '/status':
            # Auto-detect scanner device (USB number changes on re-plug)
            detect = subprocess.run(
                ['scanimage', '-L'],
                capture_output=True, text=True, timeout=15
            )
            scanner_dev = None
            for line in detect.stdout.split('\n'):
                if 'ES-400II' in line:
                    scanner_dev = line.split("'")[1] if "'" in line else line.split('`')[1].split("'")[0]
            scanner = type('obj', (object,), {
                'returncode': 0 if scanner_dev else 1,
                'stdout': f'device: {scanner_dev}' if scanner_dev else '',
                'stderr': 'ES-400II not detected on USB'
            })()
            printer = subprocess.run(
                ['lpstat', '-p', 'EPSON_ET2400'],
                capture_output=True, text=True, timeout=5
            )
            batches = sorted(glob.glob(f"{SCAN_DIR}/batch_*"))
            self._json(200, {
                'scanner': {
                    'device': 'Epson ES-400II (USB)',
                    'status': 'ready' if scanner.returncode == 0 else 'error',
                    'detail': scanner.stdout.strip() or scanner.stderr.strip()
                },
                'printer': {
                    'device': 'Epson ET-2400 (.200)',
                    'status': printer.stdout.strip()
                },
                'batches': len(batches),
                'last_scan': os.path.basename(batches[-1]) if batches else None,
                'timestamp': datetime.now().isoformat()
            })

        elif url.path == '/scan':
            tag = params.get('tag', ['auto'])[0]
            result = subprocess.run(
                [f'{SCRIPT_DIR}/epson-scan.sh', tag],
                capture_output=True, text=True, timeout=120
            )
            self._json(200, {
                'action': 'scan',
                'tag': tag,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'returncode': result.returncode
            })

        elif url.path == '/print':
            filepath = params.get('file', [None])[0]
            title = params.get('title', ['Gaia Print'])[0]
            if not filepath or not os.path.exists(filepath):
                self._json(400, {'error': f'file not found: {filepath}'})
                return
            result = subprocess.run(
                [f'{SCRIPT_DIR}/epson-print.sh', filepath, title],
                capture_output=True, text=True, timeout=60
            )
            self._json(200, {
                'action': 'print',
                'file': filepath,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'returncode': result.returncode
            })

        elif url.path == '/scans':
            batches = sorted(glob.glob(f"{SCAN_DIR}/batch_*"))
            result = []
            for b in batches:
                manifest = os.path.join(b, 'manifest.json')
                if os.path.exists(manifest):
                    with open(manifest) as f:
                        result.append(json.load(f))
                else:
                    pages = glob.glob(os.path.join(b, '*.png'))
                    result.append({'dir': os.path.basename(b), 'pages': len(pages)})
            self._json(200, {'batches': result})

        else:
            self._json(404, {'error': 'unknown endpoint', 'endpoints': ['/status', '/scan', '/print', '/scans']})

    def do_POST(self):
        url = urlparse(self.path)
        if url.path == '/print':
            length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(length).decode()
            params = parse_qs(url.query)
            title = params.get('title', ['Gaia Print'])[0]

            tmpfile = f"/tmp/gaia-print-{datetime.now().strftime('%Y%m%d%H%M%S')}.txt"
            with open(tmpfile, 'w') as f:
                f.write(body)

            result = subprocess.run(
                [f'{SCRIPT_DIR}/epson-print.sh', tmpfile, title],
                capture_output=True, text=True, timeout=60
            )
            os.unlink(tmpfile)
            self._json(200, {
                'action': 'print',
                'chars': len(body),
                'stdout': result.stdout,
                'stderr': result.stderr,
                'returncode': result.returncode
            })
        else:
            self._json(404, {'error': 'POST only on /print'})

    def log_message(self, format, *args):
        print(f"[epson] {self.client_address[0]} {format % args}")

if __name__ == '__main__':
    os.makedirs(SCAN_DIR, exist_ok=True)
    os.makedirs(PRINT_DIR, exist_ok=True)
    server = http.server.HTTPServer(('0.0.0.0', PORT), EpsonHandler)
    print(f"🦷🖨 Gaia Epson daemon on :{PORT}")
    print(f"   GET  /status  — check both devices")
    print(f"   GET  /scan    — trigger ADF scan")
    print(f"   GET  /print   — print a file")
    print(f"   POST /print   — print text body")
    print(f"   GET  /scans   — list all batches")
    server.serve_forever()


# === SOLAR PANEL ENDPOINT (added for frameGate) ===
# Original class is EpsonHandler — monkey-patch POST to also handle /solar
_orig_post = EpsonHandler.do_POST
def _new_post(self):
    from urllib.parse import urlparse
    url = urlparse(self.path)
    if url.path == '/solar':
        import os
        length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(length)
        solar_file = "/home/eastgate/Development/ecoPrimals/data/body/frame-solar-feed.jsonl"
        with open(solar_file, 'a') as f:
            f.write(body.decode() + '\n')
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(b'{"ok": true, "stored": "frame-solar-feed.jsonl"}')
        return
    _orig_post(self)
EpsonHandler.do_POST = _new_post
