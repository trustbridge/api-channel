from urllib.parse import urljoin

from flask import Flask, url_for
from libtrustbridge.errors import handlers

from api import loggers
from api.conf import Config


def create_app(config_object=None):
    if config_object is None:
        config_object = Config

    app = Flask(__name__)
    app.config.from_object(config_object)
    app.logger = loggers.create_logger(app.config)

    with app.app_context():
        from api import views

        app.register_blueprint(views.blueprint)

        handlers.register(app)

        with app.test_request_context():
            app.config['HUB_URL'] = urljoin(
                app.config['SERVICE_URL'],
                url_for('views.subscriptions_by_jurisdiction', _external=False)
            )

    return app
