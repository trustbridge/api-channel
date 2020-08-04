from api.app import create_app
from api.conf import Config

app = create_app(Config())
