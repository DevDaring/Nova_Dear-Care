#!/usr/bin/env python3
"""
verdict_server.py — Lightweight HTTP server for serving verdicts to the Fit-U Flutter app.

Runs on the RDK device. The Flutter app polls GET /api/verdicts to receive
real-time verdict notifications without requiring Firebase or API Gateway.

Endpoints:
  GET  /api/verdicts              — list all verdicts
  GET  /api/verdicts?worker_id=X  — filter by worker
  GET  /api/health                — health check
"""

import json
import logging
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

logger = logging.getLogger(__name__)

_verdicts = []
_lock = threading.Lock()


class _VerdictHandler(BaseHTTPRequestHandler):
    """Handles GET requests for verdict data."""

    def do_GET(self):
        parsed = urlparse(self.path)

        if parsed.path == '/api/verdicts':
            params = parse_qs(parsed.query)
            worker_id = params.get('worker_id', [None])[0]

            with _lock:
                if worker_id:
                    results = [v for v in _verdicts if v.get('worker_id') == worker_id]
                else:
                    results = list(_verdicts)

            self._json_response(200, results)

        elif parsed.path == '/api/health':
            self._json_response(200, {"status": "ok", "verdicts": len(_verdicts)})

        else:
            self._json_response(404, {"error": "not found"})

    def do_OPTIONS(self):
        self.send_response(200)
        self._cors_headers()
        self.end_headers()

    def _json_response(self, status, data):
        body = json.dumps(data).encode()
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(body)))
        self._cors_headers()
        self.end_headers()
        self.wfile.write(body)

    def _cors_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')

    def log_message(self, format, *args):
        pass  # Suppress default HTTP logs


def add_verdict(verdict: dict):
    """Add a verdict to the in-memory store. Called from main.py after Lambda processing."""
    with _lock:
        _verdicts.append(verdict)
        # Keep only last 50 verdicts
        while len(_verdicts) > 50:
            _verdicts.pop(0)
    logger.info("[VERDICT-SERVER] Added verdict: %s", verdict.get("encounter_id", "?"))


def start_server(port: int = 8080) -> HTTPServer:
    """Start the verdict HTTP server in a background daemon thread."""
    server = HTTPServer(('0.0.0.0', port), _VerdictHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True, name="verdict-server")
    thread.start()
    logger.info("[VERDICT-SERVER] Listening on 0.0.0.0:%d", port)
    return server
