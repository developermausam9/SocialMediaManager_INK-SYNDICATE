import os
import logging
from http.server import HTTPServer, BaseHTTPRequestHandler
from threading import Thread

logger = logging.getLogger(__name__)

class SimpleHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write(b"Bot is alive and polling!")
        
    def log_message(self, format, *args):
        # Suppress GET request logs to avoid spamming the console
        pass

def run_server():
    port = int(os.environ.get("PORT", 8080))
    try:
        server = HTTPServer(('0.0.0.0', port), SimpleHandler)
        logger.info(f"Keep-alive dummy server listening on port {port}")
        server.serve_forever()
    except Exception as e:
        logger.error(f"Failed to start keep-alive server: {e}")

def keep_alive():
    """Starts a dummy web server in a background thread to satisfy Render.com health checks."""
    t = Thread(target=run_server, daemon=True)
    t.start()
