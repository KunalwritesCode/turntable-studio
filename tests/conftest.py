import functools
import http.server
import threading

import pytest
from fixture_frames import build_fixture_site


class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, format, *args):  # noqa: A002 - signature set by the base class
        pass


class FixtureServer(http.server.ThreadingHTTPServer):
    # The player requests every frame at once; the default backlog of 5
    # resets connections under that burst before a thread can accept them.
    request_queue_size = 128


@pytest.fixture(scope="session")
def site_dir(tmp_path_factory):
    """A throwaway site: the current player files plus synthetic frames."""
    return build_fixture_site(tmp_path_factory.mktemp("site"))


@pytest.fixture(scope="session")
def site_url(site_dir):
    """Serve site_dir over HTTP on a free local port."""
    handler = functools.partial(QuietHandler, directory=str(site_dir))
    server = FixtureServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{server.server_address[1]}/"
    server.shutdown()
