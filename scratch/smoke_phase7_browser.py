import os
import sys
import json
import time
import subprocess
import urllib.request
import websocket

sys.path.insert(0, r'C:\AI-Student-Learning-Mentor')
from app import create_app

app = create_app()
serializer = app.session_interface.get_signing_serializer(app)
auth_cookie = serializer.dumps({
    'user_id': 2019,
    'user_name': 'Subham Kumar Dash',
    'user_email': 'subhamkumardash000@gmail.com',
    'user_role': 'student',
    '_fresh': True
})

server_path = r'C:\Users\subha\.gemini\antigravity\brain\a7ea8187-97b6-436d-8daf-9e8957a86e34\scratch\server_runner.py'
server = subprocess.Popen([r'python', server_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
time.sleep(2)

temp_profile = os.path.join(os.environ.get('TEMP', 'C:\\temp'), 'chrome_p7_smoke')
os.makedirs(temp_profile, exist_ok=True)

chrome = subprocess.Popen([
    r'C:\Program Files\Google\Chrome\Application\chrome.exe',
    '--headless=new',
    '--disable-gpu',
    '--no-sandbox',
    '--remote-debugging-port=9222',
    '--remote-allow-origins=*',
    f'--user-data-dir={temp_profile}',
    'about:blank'
], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
time.sleep(2)

test_pages = [
    ('/', False, 'Landing Page'),
    ('/login', False, 'Login Page'),
    ('/dashboard', True, 'Student Dashboard'),
    ('/study-plans/472', True, 'Study Plan Detail'),
    ('/quizzes/topic/1', True, 'Quiz Briefing (Phase 5.2 Fix)'),
    ('/quiz/1/start', True, 'Active Quiz Taking'),
    ('/ai', True, 'AI Mentor Chat'),
    ('/non-existent-sample', False, '404 Error Page'),
    ('/test-500', False, '500 Error Page')
]

smoke_results = []

try:
    for path, auth, label in test_pages:
        url = f"http://127.0.0.1:5000{path}"
        req = urllib.request.Request("http://127.0.0.1:9222/json/new?about:blank", method="PUT")
        with urllib.request.urlopen(req) as resp:
            target = json.loads(resp.read().decode('utf-8'))
        tid = target['id']
        ws = websocket.create_connection(target['webSocketDebuggerUrl'], timeout=10)

        mid = [1]
        def cdp(method, params=None):
            m = mid[0]
            mid[0] += 1
            ws.send(json.dumps({'id': m, 'method': method, 'params': params or {}}))
            while True:
                msg = json.loads(ws.recv())
                if msg.get('id') == m:
                    return msg.get('result', {})

        cdp('Page.enable')
        cdp('Runtime.enable')

        if auth:
            cdp('Network.setCookie', {
                'name': 'session',
                'value': auth_cookie,
                'domain': '127.0.0.1',
                'path': '/'
            })

        cdp('Emulation.setDeviceMetricsOverride', {'width': 1366, 'height': 768, 'deviceScaleFactor': 1, 'mobile': False})
        cdp('Page.navigate', {'url': url})
        time.sleep(0.7)

        title = cdp('Runtime.evaluate', {'expression': 'document.title'})['result'].get('value', '')
        scroll_w = cdp('Runtime.evaluate', {'expression': 'document.documentElement.scrollWidth'})['result'].get('value', 0)
        inner_w = cdp('Runtime.evaluate', {'expression': 'window.innerWidth'})['result'].get('value', 0)
        h_overflow = scroll_w > inner_w
        err_code = cdp('Runtime.evaluate', {'expression': 'document.querySelector(".error-code") ? document.querySelector(".error-code").innerText : ""'})['result'].get('value', '')

        ws.close()
        urllib.request.urlopen(f"http://127.0.0.1:9222/json/close/{tid}")

        status = 'PASS'
        if '500' in title and path != '/test-500':
            status = 'FAIL'

        smoke_results.append({
            'path': path,
            'label': label,
            'title': title,
            'overflow': h_overflow,
            'status': status,
            'err_code': err_code
        })
        print(f"  [{status}] {label:30s} -> Title: '{title[:35]}' | Overflow: {h_overflow}")

finally:
    chrome.terminate()
    server.terminate()
    print("\nPhase 7 Chrome Smoke Suite Completed.")
