from unittest import mock

import pytest
from flask import url_for
from libtrustbridge.websub.repos import NotificationsRepo
from responses import Response

from api.models import Message, MessageStatus
from api.use_cases import SendMessageToForeignUseCase, SendMessageFailure, ProcessMessageUseCase, PublishNewMessageUseCase


class TestSendMessageToForeignUseCase:
    @pytest.fixture(autouse=True)
    def setup(self, mocked_responses):
        self.mocked_responses = mocked_responses
        self.endpoint = 'http://foreign_endpoint.com'
        self.message = Message(payload={"receiver": "AU"})

    def test_send__when_responded_OK__should_set_status_as_delivered(self):
        self.mocked_responses.add(
            Response(method='POST', url=self.endpoint)
        )
        use_case = SendMessageToForeignUseCase(self.endpoint)
        use_case.send(self.message)

        assert self.message.status == MessageStatus.DELIVERED
        assert len(self.mocked_responses.calls) == 1
        assert self.mocked_responses.calls[0].request.body == b'{"receiver": "AU"}'

    def test_send__when_responded_not_OK__should_raise_exception(self):
        self.mocked_responses.add(
            Response(method='POST', url=self.endpoint, status=400)
        )
        use_case = SendMessageToForeignUseCase(self.endpoint)
        with pytest.raises(SendMessageFailure):
            use_case.send(self.message)


@pytest.mark.usefixtures("client_class", "clean_channel_repo", "clean_channel_queue_repo", "mocked_responses")
class TestProcessMessageUseCase:
    message_data = {
        "sender": "AU",
        "receiver": "CN",
        "subject": "AU.abn0000000000.XXXX-XXXXX-XXXXX-XXXXXX",
        "obj": "QmQtYtUS7K1AdKjbuMsmPmPGDLaKL38M5HYwqxW9RKW49n",
        "predicate": "UN.CEFACT.Trade.CertificateOfOrigin.created"
    }
    endpoint = 'http://foreign_endpoint.com'

    def test_process_message__when_not_delivered__should_try_to_deliver(self):
        self.mocked_responses.add(
            Response(method='POST', url=self.endpoint)
        )
        use_case = ProcessMessageUseCase(self.channel_repo, self.channel_queue_repo, self.endpoint)
        self.client.post(url_for('views.post_message'), json=self.message_data)
        use_case.execute()

        assert len(self.mocked_responses.calls) == 1
        assert self.mocked_responses.calls[0].request.body == b'{"obj": "QmQtYtUS7K1AdKjbuMsmPmPGDLaKL38M5HYwqxW9RKW49n", "predicate": "UN.CEFACT.Trade.CertificateOfOrigin.created", "receiver": "CN", "sender": "AU", "subject": "AU.abn0000000000.XXXX-XXXXX-XXXXX-XXXXXX"}'


class TestPublishNewMessageUseCase:
    def test_use_case__should_send_message_to_notification_queue(self):
        notifications_repo = mock.create_autospec(NotificationsRepo).return_value

        message = Message(id=24, status=MessageStatus.CONFIRMED, payload={'sender': 'CN'})
        PublishNewMessageUseCase('AU', notifications_repo).publish(message=message)

        notifications_repo.post_job.assert_called_once_with({
            'topic': 'jurisdiction.AU',
            'content': {
                'id': 24
            }
        })
