from decouple import config
from libtrustbridge.utils.conf import env_s3_config, env_queue_config


class Config:
    DEBUG = config('DEBUG', default=True, cast=bool)
    TESTING = config('TESTING', default=False, cast=bool)

    SERVICE_NAME = config('SERVICE_NAME', default='api-channel')
    JURISDICTION = config("JURISDICTION", default='AU')
    SERVICE_URL = config("SERVICE_URL", default='http://api-channel')
    FOREIGN_ENDPOINT_URL = config("FOREIGN_ENDPOINT_URL", default='http://foreign-api-channel/incoming/messages')

    CHANNEL_REPO_CONF = env_s3_config('CHANNEL_REPO')
    CHANNEL_QUEUE_REPO_CONF = env_queue_config('CHANNEL_QUEUE_REPO')

    SUBSCRIPTIONS_REPO_CONF = env_s3_config('SUBSCRIPTIONS_REPO')
    NOTIFICATIONS_REPO_CONF = env_queue_config('NOTIFICATIONS_REPO')
    DELIVERY_OUTBOX_REPO_CONF = env_queue_config('DELIVERY_OUTBOX_REPO')

    LOG_FORMATTER_JSON = False

