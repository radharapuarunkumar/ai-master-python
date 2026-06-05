"""
Robust development server for the AI Master Python frontend.
- Suppresses ConnectionAbortedError / BrokenPipeError (Windows harmless noise)
- Forces UTF-8 stdout so Windows cp1252 consoles never crash
- Uses ThreadingTCPServer so each request gets its own thread

Usage:
    python serve.py [PORT]       default port: 3000
"""
import http.server
import socketserver
import os
import sys
from pathlib import Path

# ── UTF-8 stdout/stderr so Windows cp1252 never raises UnicodeEncodeError ──
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 3000
PROJECT_ROOT = Path(__file__).parent          # ai-master-python/


class SilentCORSHandler(http.server.SimpleHTTPRequestHandler):
    """Serves files from PROJECT_ROOT with CORS headers.
    Swallows harmless Windows connection-abort noise."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(PROJECT_ROOT), **kwargs)

    # ── CORS ──────────────────────────────────────────────────────────────
    def end_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

    # ── Suppress asset request noise ────────────────────────────────────
    def log_message(self, fmt, *args):
        try:
            msg = fmt % args
            skip = (".css", ".js", ".png", ".jpg", ".ico", ".woff", ".ttf", ".svg")
            if any(s in msg for s in skip):
                return
            print(f"  {msg}", flush=True)
        except Exception:
            pass

    # ── Suppress harmless Windows broken-pipe errors ─────────────────────
    def handle_error(self, request, client_address):
        exc = sys.exc_info()[1]
        benign = (ConnectionAbortedError, ConnectionResetError, BrokenPipeError)
        if isinstance(exc, benign):
            return          # silently drop — client closed the tab/request
        if hasattr(exc, 'winerror') and exc.winerror in (10053, 10054):
            return          # WinError 10053/10054 — same thing on Windows
        super().handle_error(request, client_address)


class ThreadedServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    allow_reuse_address = True
    daemon_threads = True


def main():
    os.chdir(PROJECT_ROOT)
    pages = [
        ("Landing",   f"http://localhost:{PORT}/frontend/index.html"),
        ("Login",     f"http://localhost:{PORT}/frontend/pages/login.html"),
        ("Dashboard", f"http://localhost:{PORT}/frontend/pages/dashboard.html"),
        ("Courses",   f"http://localhost:{PORT}/frontend/pages/courses.html"),
        ("Lesson",    f"http://localhost:{PORT}/frontend/pages/lesson.html"),
        ("Progress",  f"http://localhost:{PORT}/frontend/pages/progress.html"),
        ("AI Chat",   f"http://localhost:{PORT}/frontend/pages/chat.html"),
    ]
    width = max(len(label) for label, _ in pages)
    lines = ["", "  AI Master Python -- Frontend Dev Server",
             f"  Serving from: {PROJECT_ROOT}", ""]
    for label, url in pages:
        lines.append(f"  {label:<{width}}  {url}")
    lines += ["", f"  API backend expected at: http://localhost:8000",
              "  Press Ctrl+C to stop.", ""]
    print("\n".join(lines), flush=True)

    with ThreadedServer(("", PORT), SilentCORSHandler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nServer stopped.")


if __name__ == "__main__":
    main()
