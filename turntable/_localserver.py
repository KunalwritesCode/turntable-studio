"""Serves a local directory over HTTP, for the renderer and for tests."""

import contextlib
import functools
import http.server
import threading
from pathlib import Path


class _QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, format, *args):  # noqa: A002 - signature set by the base class
        pass


class _Server(http.server.ThreadingHTTPServer):
    # default backlog (5) resets connections under a burst of many requests at once
    request_queue_size = 128


@contextlib.contextmanager
def serve_directory(directory: Path):
    """Serve `directory` on a free local port; yields its base URL."""
    handler = functools.partial(_QuietHandler, directory=str(directory))
    server = _Server(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_address[1]}/"
    finally:
        server.shutdown()
