import pytest
import responses

from api.app import create_app
from api.conf import Config
from api.repos import ChannelRepo, ChannelQueueRepo


@pytest.fixture(scope='session')
def app():
    yield create_app(Config())


@pytest.fixture
def mocked_responses(request):
    with responses.RequestsMock() as rsps:
        if request.cls is not None:
            request.cls.mocked_responses = rsps
        yield rsps


@pytest.fixture
def clean_channel_repo(app, request):
    repo = ChannelRepo(app.config['CHANNEL_REPO_CONF'])
    repo._unsafe_method__clear()
    if request.cls is not None:
        request.cls.channel_repo = repo
    yield repo
    repo._unsafe_method__clear()


@pytest.fixture
def clean_channel_queue_repo(app, request):
    repo = ChannelQueueRepo(app.config['CHANNEL_QUEUE_REPO_CONF'])
    repo._unsafe_method__clear()
    if request.cls is not None:
        request.cls.channel_queue_repo = repo
    yield repo
    repo._unsafe_method__clear()
