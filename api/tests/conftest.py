import pytest
import responses

from api.app import create_app
from api.conf import Config


@pytest.fixture(scope='session')
def app():
    yield create_app(Config())


@pytest.fixture
def mocked_responses(request):
    with responses.RequestsMock() as rsps:
        if request.cls is not None:
            request.cls.mocked_responses = rsps
        yield rsps
