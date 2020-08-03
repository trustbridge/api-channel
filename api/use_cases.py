import logging
import random

import requests
from libtrustbridge.utils import get_retry_time
from libtrustbridge.websub import repos
from libtrustbridge.websub.domain import Pattern

from api.models import MessageStatus, Message
from api.repos import ChannelRepo, ChannelQueueRepo

logger = logging.getLogger(__name__)


class ReceiveMessageUseCase:
    def __init__(self, channel_repo: ChannelRepo, channel_queue_repo: ChannelQueueRepo):
        self.channel_repo = channel_repo
        self.queue_repo = channel_queue_repo

    def receive(self, message: Message):
        message = self.channel_repo.save_message(message)
        self.queue_repo.enqueue(str(message.id))
        return message


class SendMessageFailure(Exception):
    pass


class SendMessageToForeignUseCase:
    def __init__(self, foreign_endpoint):
        self.foreign_endpoint = foreign_endpoint

    def send(self, message: Message):
        response = requests.post(url=self.foreign_endpoint, json=message.payload)
        if response.status_code == 200:
            message.status = MessageStatus.DELIVERED
            return

        raise SendMessageFailure("Foreign endpoint responded with non-OK response (%d): %r" % (response.status_code, response.text))


class ProcessMessageUseCase:
    """
    Given new job appears in the queue, get message from the repo and try to send it
    """
    MAX_ATTEMPTS = 3

    def __init__(self, channel_repo: ChannelRepo, channel_queue_repo: ChannelQueueRepo, foreign_endpoint):
        self.channel_repo = channel_repo
        self.queue_repo = channel_queue_repo
        self.use_case = SendMessageToForeignUseCase(foreign_endpoint)

    def execute(self):
        job = self.queue_repo.get_job()
        if not job:
            return
        return self.process(*job)

    def process(self, job_id, payload):
        message_id = payload['message_id']
        attempt = payload['retry']

        message = self.channel_repo.get_message(message_id)
        logger.info("Processing message with message_id [%s], attempt: %d,  %r", message_id, attempt, message)
        if message.status == MessageStatus.DELIVERED:
            return

        try:
            self.use_case.send(message)
            self.channel_repo.save_message(message)
        except SendMessageFailure:
            logger.info("[%s] sending message failed", job_id)
            if attempt < self.MAX_ATTEMPTS:
                logger.info("[%s] re-schedule sending message", job_id)
                self.queue_repo.enqueue(message_id, attempt + 1)


class SubscriptionRegisterUseCase:
    """
    Used by the subscription API

    Initialised with the subscription repo,
    saves url, pattern, expiration to the storage.
    """

    def __init__(self, subscriptions_repo: repos.SubscriptionsRepo):
        self.subscriptions_repo = subscriptions_repo

    def execute(self, url, topic, expiration=None):
        # this operation deletes all previous subscription for given url and pattern
        # and replaces them with new one. Techically it's create or update operation

        self.subscriptions_repo.subscribe_by_pattern(Pattern(topic), url, expiration)


class SubscriptionNotFound(Exception):
    pass


class SubscriptionDeregisterUseCase:
    """
    Used by the subscription API

    on user's request removes the subscription to given url for given pattern
    """

    def __init__(self, subscriptions_repo: repos.SubscriptionsRepo):
        self.subscriptions_repo = subscriptions_repo

    def execute(self, url, topic):
        pattern = Pattern(topic)
        subscriptions = self.subscriptions_repo.get_subscriptions_by_pattern(pattern)
        subscriptions_by_url = [s for s in subscriptions if s.callback_url == url]
        if not subscriptions_by_url:
            raise SubscriptionNotFound()
        self.subscriptions_repo.bulk_delete([pattern.to_key(url)])


class PublishNewMessageUseCase:
    """
    Given new message,
    message id should be posted for notification"""

    def __init__(self, endpoint, notification_repo: repos.NotificationsRepo):
        self.notifications_repo = notification_repo
        self.endpoint = endpoint

    def publish(self, message_payload):
        job_payload = {
            'topic': f'jurisdiction.{self.endpoint}',
            'content': message_payload
        }
        logger.debug('publish notification %r', job_payload)
        self.notifications_repo.post_job(job_payload)


class DispatchMessageToSubscribersUseCase:
    """
    Used by the callbacks spreader worker.

    This is the "fan-out" part of the WebSub,
    where each event dispatched
    to all the relevant subscribers.
    For each event (notification),
    it looks-up the relevant subscribers
    and dispatches a callback task
    so that they will be notified.

    There is a downstream delivery processor
    that actually makes the callback,
    it is insulated from this process
    by the delivery outbox message queue.

    """

    def __init__(
            self, notifications_repo: repos.NotificationsRepo,
            delivery_outbox_repo: repos.DeliveryOutboxRepo,
            subscriptions_repo: repos.SubscriptionsRepo):
        self.notifications = notifications_repo
        self.delivery_outbox = delivery_outbox_repo
        self.subscriptions = subscriptions_repo

    def execute(self):
        job = self.notifications.get_job()
        if not job:
            return
        return self.process(*job)

    def process(self, msg_id, payload):
        subscriptions = self._get_subscriptions(payload['topic'])

        content = payload['content']

        for subscription in subscriptions:
            if not subscription.is_valid:
                logger.info("Found invalid subscription %s", subscription)
                continue
            job = {
                's': subscription.callback_url,
                'payload': content,
            }
            logger.info(
                "Will be notifying '%s' with '%s'",
                subscription.callback_url, content
            )
            self.delivery_outbox.post_job(job)

        self.notifications.delete(msg_id)

    def _get_subscriptions(self, topic):
        pattern = repos.Pattern(topic)
        subscribers = self.subscriptions.get_subscriptions_by_pattern(pattern)
        if not subscribers:
            logger.info("Nobody to notify about the topic %s", topic)
        else:
            logger.info("The topic %s has %s subscriber(s)", topic, len(subscribers))
        return subscribers


class InvalidCallbackResponse(Exception):
    pass


class DeliverCallbackUseCase:
    """
    Is used by a callback deliverer worker

    Reads queue delivery_outbox_repo consisting of tasks in format:
        (url, message)

    Then such message should be either sent to this URL and the task is deleted
    or, in case of any error, not to be re-scheduled again
    (up to MAX_ATTEMPTS times)

    """

    MAX_ATTEMPTS = 3

    def __init__(self, delivery_outbox_repo: repos.DeliveryOutboxRepo, hub_url):
        self.delivery_outbox = delivery_outbox_repo
        self.hub_url = hub_url

    def execute(self):
        deliverable = self.delivery_outbox.get_job()
        if not deliverable:
            return

        queue_msg_id, payload = deliverable
        return self.process(queue_msg_id, payload)

    def process(self, queue_msg_id, job):
        subscribe_url = job['s']
        payload = job['payload']
        attempt = int(job.get('retry', 1))

        try:
            logger.debug('[%s] deliver notification to %s with payload: %s (attempt %s)',
                         queue_msg_id, subscribe_url, payload, attempt)
            self._deliver_notification(subscribe_url, payload)
        except InvalidCallbackResponse as e:
            logger.info("[%s] delivery failed", queue_msg_id)
            logger.exception(e)
            if attempt < self.MAX_ATTEMPTS:
                logger.info("[%s] re-schedule delivery", queue_msg_id)
                self._retry(subscribe_url, payload, attempt)

        self.delivery_outbox.delete(queue_msg_id)

    def _retry(self, subscribe_url, payload, attempt):
        logger.info("Delivery failed, re-schedule it")
        job = {'s': subscribe_url, 'payload': payload, 'retry': attempt + 1}
        self.delivery_outbox.post_job(job, delay_seconds=get_retry_time(attempt))

    def _deliver_notification(self, url, payload):
        """
        Send the payload to subscriber's callback url

        https://indieweb.org/How_to_publish_and_consume_WebSub
        https://www.w3.org/TR/websub/#x7-content-distribution
        """

        logger.info("Sending WebSub payload \n    %s to callback URL \n    %s", payload, url)
        header = {
            'Link': f'<{self.hub_url}>; rel="hub"'
        }
        try:
            resp = requests.post(url, json=payload, headers=header)
            if str(resp.status_code).startswith('2'):
                return
        except ConnectionError:
            raise InvalidCallbackResponse("Connection error, url: %s", url)

        raise InvalidCallbackResponse("Subscription url %s seems to be invalid, "
                                      "returns %s", url, resp.status_code)

    @staticmethod
    def _get_retry_time(attempt):
        """exponential back off with jitter"""
        base = 8
        max_retry = 100
        delay = min(base * 2 ** attempt, max_retry)
        jitter = random.uniform(0, delay / 2)
        return int(delay / 2 + jitter)
