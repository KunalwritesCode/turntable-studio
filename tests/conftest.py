import pytest
from fixture_frames import build_fixture_site

from turntable._localserver import serve_directory


@pytest.fixture(scope="session")
def site_dir(tmp_path_factory):
    """A throwaway site: the current player files plus synthetic frames."""
    return build_fixture_site(tmp_path_factory.mktemp("site"))


@pytest.fixture(scope="session")
def site_url(site_dir):
    """Serve site_dir over HTTP on a free local port."""
    with serve_directory(site_dir) as base_url:
        yield base_url
