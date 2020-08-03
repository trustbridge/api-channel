import logging
import uuid

from libtrustbridge.repos.elasticmqrepo import ElasticMQRepo
from libtrustbridge.repos.miniorepo import MinioRepo
from libtrustbridge.utils import get_retry_time

from api.models import MessageSchema

logger = logging.getLogger(__name__)


class ChannelRepo(MinioRepo):
    DEFAULT_BUCKET = 'channel'

    def get_message(self, message_id):
        path = self._get_message_path(message_id)
        try:
            message_json = self.get_object_content(path)
        except self.client.exceptions.NoSuchKey:
            logger.warning("Message not found, path: %s", path)
            return
        return MessageSchema().loads(message_json)

    def save_message(self, message):
        message.id = message.id or uuid.uuid4()
        body = MessageSchema().dumps(message)
        path = self._get_message_path(message.id)
        self.put_object(chunked_path=path, content_body=body)
        return message

    def _get_message_path(self, message_id):
        return f'messages/{message_id}'


class ChannelQueueRepo(ElasticMQRepo):
    def _get_queue_name(self):
        return 'channel-messages'

    def enqueue(self, message_id, attempt=1):
        logger.debug('enqueue message, message_id: %s', message_id)
        self.post_job({
            'message_id': message_id,
            'retry': attempt,
        }, delay_seconds=get_retry_time(attempt))
