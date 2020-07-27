import logging
import time

from flask_script import Command
from libtrustbridge.websub import repos
from libtrustbridge.websub.processors import Processor

from api import use_cases

logger = logging.getLogger(__name__)


class RunProcessorCommand(Command):

    def __call__(self, app=None, *args, **kwargs):
        self.app = app
        return super().__call__(app, *args, **kwargs)

    def run(self):
        logger.info('Starting processor %s', self.__class__.__name__)
        processor = self.get_processor()
        logger.info('Run processor for use case "%s"', processor.use_case.__class__.__name__)

        for result in processor:
            if result is None:
                time.sleep(1)

    def get_processor(self):
        raise NotImplementedError


class RunCallbackSpreaderProcessorCommand(RunProcessorCommand):
    """
    Convert each incoming message to set of messages containing (websub_url, message)
    so they may be sent and fail separately
    """

    def get_processor(self):
        config = self.app.config
        notifications_repo = repos.NotificationsRepo(config['NOTIFICATIONS_REPO_CONF'])
        delivery_outbox_repo = repos.DeliveryOutboxRepo(config['DELIVERY_OUTBOX_REPO_CONF'])
        subscriptions_repo = repos.SubscriptionsRepo(config.get('SUBSCRIPTIONS_REPO_CONF'))
        use_case = use_cases.DispatchMessageToSubscribersUseCase(
            notifications_repo=notifications_repo,
            delivery_outbox_repo=delivery_outbox_repo,
            subscriptions_repo=subscriptions_repo,
        )
        return Processor(use_case=use_case)


class RunCallbackDeliveryProcessorCommand(RunProcessorCommand):
    """
    Iterate over the DeliverCallbackUseCase.
    """

    def get_processor(self):
        config = self.app.config
        delivery_outbox_repo = repos.DeliveryOutboxRepo(config['DELIVERY_OUTBOX_REPO_CONF'])

        use_case = use_cases.DeliverCallbackUseCase(
            delivery_outbox_repo=delivery_outbox_repo,
            hub_url=config['HUB_URL'],
        )
        return Processor(use_case=use_case)
