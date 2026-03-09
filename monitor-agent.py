#!/usr/bin/env python3
"""
ParentWatch Monitor Agent
Runs on child's laptop - tracks active windows and serves dashboard
"""

import time
import json
import threading
import platform
import subprocess
import socket
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse

# ── Activity log (in-memory, last 200 entries) ─────────────────────────────
activity_log = []
current_activity = {"app": "Unknown", "title": "", "since": "", "duration": 0}
lock = threading.Lock()

def get_active_window():
    """Cross-platform active window title fetcher."""
    system = platform.system()
    try:
        if system == "Windows":
            import ctypes
            hwnd = ctypes.windll.user32.GetForegroundWindow()
            length = ctypes.windll.user32.GetWindowTextLengthW(hwnd)
            buf = ctypes.create_unicode_buffer(length + 1)
            ctypes.windll.user32.GetWindowTextW(hwnd, buf, length + 1)
            title = buf.value or "Unknown"
            # Get process name
            pid = ctypes.c_ulong()
            ctypes.windll.user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
            try:
                import psutil
                proc = psutil.Process(pid.value)
                return proc.name(), title
            except:
                return "Unknown", title

        elif system == "Darwin":  # macOS
            script = '''
            tell application "System Events"
                set frontApp to name of first application process whose frontmost is true
                set frontTitle to ""
                try
                    set frontTitle to name of front window of (first application process whose frontmost is true)
                end try
                return frontApp & "|" & frontTitle
            end tell
            '''
            result = subprocess.run(["osascript", "-e", script],
                                    capture_output=True, text=True, timeout=3)
            parts = result.stdout.strip().split("|")
            return parts[0] if parts else "Unknown", parts[1] if len(parts) > 1 else ""

        elif system == "Linux":
            # Try xdotool
            try:
                wid = subprocess.run(["xdotool", "getactivewindow"],
                                     capture_output=True, text=True, timeout=2)
                title = subprocess.run(["xdotool", "getwindowname", wid.stdout.strip()],
                                       capture_output=True, text=True, timeout=2)
                pid_r = subprocess.run(["xdotool", "getwindowpid", wid.stdout.strip()],
                                       capture_output=True, text=True, timeout=2)
                app = "Unknown"
                if pid_r.stdout.strip():
                    cmd = subprocess.run(["ps", "-p", pid_r.stdout.strip(), "-o", "comm="],
                                        capture_output=True, text=True)
                    app = cmd.stdout.strip()
                return app, title.stdout.strip()
            except:
                return "Unknown", "xdotool not found"
    except Exception as e:
        return "Unknown", str(e)

def categorize(app_name, title):
    app = (app_name + " " + title).lower()
    if any(x in app for x in ["chrome", "firefox", "safari", "edge", "browser"]):
        if any(x in app for x in ["youtube", "netflix", "twitch", "tiktok", "instagram", "facebook", "twitter", "x.com"]):
            return "⚠️ Social/Entertainment", "red"
        if any(x in app for x in ["stackoverflow", "github", "docs", "learn", "edu", "khan", "coursera"]):
            return "✅ Educational", "green"
        return "🌐 Browsing", "yellow"
    if any(x in app for x in ["code", "vscode", "pycharm", "intellij", "notepad", "sublime", "atom"]):
        return "💻 Coding/Dev", "green"
    if any(x in app for x in ["word", "excel", "powerpoint", "docs.google", "notion", "obsidian"]):
        return "📝 Productivity", "green"
    if any(x in app for x in ["game", "steam", "epic", "roblox", "minecraft", "fortnite", "valorant"]):
        return "🎮 Gaming", "red"
    if any(x in app for x in ["discord", "whatsapp", "telegram", "slack", "zoom", "teams", "skype"]):
        return "💬 Communication", "yellow"
    if any(x in app for x in ["spotify", "music", "vlc", "media"]):
        return "🎵 Media", "yellow"
    return "📁 Other", "gray"

def monitor_loop():
    global current_activity, activity_log
    last_app = None
    last_title = None
    start_time = datetime.now()

    while True:
        app, title = get_active_window()
        now = datetime.now()

        if app != last_app or title != last_title:
            if last_app is not None:
                duration = int((now - start_time).total_seconds())
                cat, color = categorize(last_app, last_title)
                entry = {
                    "app": last_app,
                    "title": last_title[:80],
                    "category": cat,
                    "color": color,
                    "started": start_time.strftime("%H:%M:%S"),
                    "duration": duration,
                    "timestamp": start_time.isoformat()
                }
                with lock:
                    activity_log.insert(0, entry)
                    if len(activity_log) > 200:
                        activity_log.pop()

            last_app = app
            last_title = title
            start_time = now

        cat, color = categorize(app, title)
        with lock:
            current_activity = {
                "app": app,
                "title": title[:80],
                "category": cat,
                "color": color,
                "since": start_time.strftime("%H:%M:%S"),
                "duration": int((now - start_time).total_seconds()),
                "timestamp": now.isoformat()
            }

        time.sleep(2)

# ── HTTP Server ─────────────────────────────────────────────────────────────
HTML_DASHBOARD = open("dashboard.html").read()

class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args): pass  # suppress logs

    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/":
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(HTML_DASHBOARD.encode())
        elif path == "/api/status":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            with lock:
                data = {
                    "current": current_activity,
                    "log": activity_log[:50],
                    "hostname": socket.gethostname(),
                    "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
            self.wfile.write(json.dumps(data).encode())
        else:
            self.send_response(404)
            self.end_headers()

def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]
    except:
        return "127.0.0.1"
    finally:
        s.close()

if __name__ == "__main__":
    print("=" * 50)
    print("  ParentWatch Monitor Agent")
    print("=" * 50)
    ip = get_local_ip()
    PORT = 8765
    print(f"\n✅ Monitor started!")
    print(f"📺 Open on Smart TV: http://{ip}:{PORT}")
    print(f"🔍 Or use IP directly: http://{ip}:{PORT}")
    print(f"\nPress Ctrl+C to stop\n")

    # Start monitoring thread
    t = threading.Thread(target=monitor_loop, daemon=True)
    t.start()

    # Start web server
    server = HTTPServer(("0.0.0.0", PORT), Handler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")
