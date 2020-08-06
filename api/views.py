import json
import logging
import uuid
from http import HTTPStatus

import marshmallow
import requests
from flask import Blueprint, Response, request
from flask import current_app
from flask.views import View
from libtrustbridge.utils.routing import mimetype
from libtrustbridge.websub.constants import MODE_ATTR_SUBSCRIBE_VALUE
from libtrustbridge.websub.exceptions import SubscriptionNotFoundError
from libtrustbridge.websub.repos import SubscriptionsRepo, NotificationsRepo
from libtrustbridge.websub.schemas import SubscriptionForm
from webargs import fields
from webargs.flaskparser import use_kwargs

from api import use_cases
from api.models import Message, MessageSchema
from api.repos import ChannelQueueRepo, ChannelRepo
from api.use_cases import ReceiveMessageUseCase

blueprint = Blueprint('views', __name__)
logger = logging.getLogger(__name__)


class JsonResponse(Response):
    default_mimetype = 'application/json'

    def __init__(self, response=None, *args, **kwargs):
        if response:
            response = json.dumps(response)

        super().__init__(response, *args, **kwargs)


@blueprint.route('/', methods=['GET'])
def index():
    data = {
        "service": current_app.config.get('SERVICE_NAME'),
    }
    # mostly for Sentry debug - this page is not loaded frequently anyway
    current_app.logger.warning("Index page is loaded")
    return JsonResponse(data)


@blueprint.route('/messages', methods=['POST'])
def post_message():
    message = Message(payload=json.loads(request.data))
    channel_repo = ChannelRepo(current_app.config['CHANNEL_REPO_CONF'])
    channel_queue_repo = ChannelQueueRepo(current_app.config['CHANNEL_QUEUE_REPO_CONF'])
    use_case = ReceiveMessageUseCase(channel_repo, channel_queue_repo)
    use_case.receive(message)
    message_data = MessageSchema().dump(message)
    return JsonResponse(message_data, status=200)


@blueprint.route('/messages/<id>')
@use_kwargs({'fields': fields.DelimitedList(fields.Str())}, location="querystring")
def get_message(id, fields=None):
    if fields == ['status']:
        channel_repo = ChannelRepo(current_app.config['CHANNEL_REPO_CONF'])
        message = channel_repo.get_message(id)
        if message:
            message_data = MessageSchema().dump(message)
            return JsonResponse({'status': message_data['status']}, status=200)
    return Response(response="{}", mimetype="application/json")


class IntentVerificationFailure(Exception):
    pass


class BaseSubscriptionsView(View):
    methods = ['POST']

    @mimetype(include=['application/x-www-form-urlencoded'])
    def dispatch_request(self):
        try:
            form_data = SubscriptionForm().load(request.form.to_dict())
        except marshmallow.ValidationError as e:  # TODO integrate marshmallow and libtrustbridge.errors.handlers
            return JsonResponse(e.messages, status=HTTPStatus.BAD_REQUEST)

        current_app.logger.info("Subscription request received: %s", form_data)

        topic = self.get_topic(form_data)
        callback = form_data['callback']
        mode = form_data['mode']
        lease_seconds = form_data['lease_seconds']
        try:
            self.verify(callback, mode, topic, lease_seconds)
        except IntentVerificationFailure:
            current_app.logger.error(
                "Intent verification failed for the %s", form_data.get("callback")
            )
            return JsonResponse({'error': 'Intent verification failed'}, status=HTTPStatus.BAD_REQUEST)

        if mode == MODE_ATTR_SUBSCRIBE_VALUE:
            current_app.logger.info(
                "Subscribed %s to %s", form_data.get("callback"), form_data.get("topic")
            )
            self._subscribe(callback, topic, lease_seconds)
        else:
            current_app.logger.info(
                "Unsubscribed %s from %s", form_data.get("callback"), form_data.get("topic")
            )
            self._unsubscribe(callback, topic)

        return JsonResponse(status=HTTPStatus.ACCEPTED)

    def get_topic(self, form_data):
        return form_data['topic']

    def _subscribe(self, callback, topic, lease_seconds):
        repo = self._get_repo()
        use_case = use_cases.SubscriptionRegisterUseCase(repo)
        use_case.execute(callback, topic, lease_seconds)

    def _unsubscribe(self, callback, topic):
        repo = self._get_repo()
        use_case = use_cases.SubscriptionDeregisterUseCase(repo)
        try:
            use_case.execute(callback, topic)
        except use_cases.SubscriptionNotFound as e:
            raise SubscriptionNotFoundError() from e

    def _get_repo(self):
        return SubscriptionsRepo(current_app.config.get('SUBSCRIPTIONS_REPO_CONF'))

    def verify(self, callback_url, mode, topic, lease_seconds):
        challenge = str(uuid.uuid4())
        params = {
            'hub.mode': mode,
            'hub.topic': topic,
            'hub.challenge': challenge,
            'hub.lease_seconds': lease_seconds
        }
        response = requests.get(callback_url, params)
        if response.status_code == 200 and response.text == challenge:
            return

        raise IntentVerificationFailure()


class SubscriptionByJurisdiction(BaseSubscriptionsView):
    """
    ---
    post:
        description:
            Subscribe to updates about new messages sent to jurisdiction (AU, SG, etc.)
        requestBody:
            content:
                application/x-www-form-urlencoded:
                    schema: SubscriptionForm
        responses:
            202:
                description: Client successfully subscribed/unsubscribed
            400:
                description: Wrong params or intent verification failure
    """

    def get_topic(self, form_data):
        return "jurisdiction.%s" % form_data['topic']


blueprint.add_url_rule(
    '/messages/subscriptions/by_jurisdiction',
    view_func=SubscriptionByJurisdiction.as_view('subscriptions_by_jurisdiction')
)


@blueprint.route('/messages/incoming', methods=['POST'])
@mimetype('application/json')
def incoming_message():
    data = json.loads(request.data.decode())
    logger.debug("Received message %r", data)
    notifications_repo = NotificationsRepo(current_app.config['NOTIFICATIONS_REPO_CONF'])
    use_case = use_cases.PublishNewMessageUseCase(current_app.config['JURISDICTION'], notifications_repo)
    use_case.publish(data)
    return JsonResponse({'status': 'delivered'}, status=200)
