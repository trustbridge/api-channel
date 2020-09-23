import pytest
from flask import url_for

from api.models import Message


@pytest.mark.usefixtures("client_class", "clean_channel_repo", "clean_channel_queue_repo")
class TestPostMessage:
    message_data = {
        "sender": "AU",
        "receiver": "CN",
        "subject": "AU.abn0000000000.XXXX-XXXXX-XXXXX-XXXXXX",
        "obj": "QmQtYtUS7K1AdKjbuMsmPmPGDLaKL38M5HYwqxW9RKW49n",
        "predicate": "UN.CEFACT.Trade.CertificateOfOrigin.created"
    }

    def test_post_message__should_enqueue_message_for_asynchronous_processing(self):
        response = self.client.post(url_for('views.post_message'), json=self.message_data)
        assert response.status_code == 200
        data = response.json
        assert data['status'] == 'received'
        assert data['payload'] == self.message_data
        assert data['id']

        job = self.channel_queue_repo.get_job()
        assert job
        job_id, payload = job
        assert payload['message_id'] == data['id']


@pytest.mark.usefixtures("client_class", "clean_channel_repo")
class TestGetMessage:
    def test_get_message__when_not_exist_should_return_empty_dict(self):
        response = self.client.get(url_for('views.get_message', id=100))
        assert response.status_code == 404
        assert response.json == {}

    def test_get_message__should_return_message_by_id(self):
        message = self.channel_repo.save_message(Message(payload={'obj': 'test'}))
        response = self.client.get(url_for('views.get_message', id=message.id))
        assert response.status_code == 200
        assert response.json == {'id': message.id, 'payload': {'obj': 'test'}, 'status': 'received'}

    def test_get_message_status__when_exist__should_return_just_status(self):
        message = self.channel_repo.save_message(Message(payload={'obj': 'test'}))
        url = url_for('views.get_message', id=str(message.id))
        response = self.client.get(f'{url}?fields=status')

        assert response.status_code == 200
        assert response.json == {'status': 'received'}


@pytest.mark.usefixtures("client_class", "clean_channel_repo")
class TestIncomingMessage:
    def test_incoming_message__should_be_saved_in_repo_and_notification_sent(self):
        message_data = {
            "sender": "AU",
            "receiver": "CN",
            "subject": "AU.abn0000000000.XXXX-XXXXX-XXXXX-XXXXXX",
            "obj": "QmQtYtUS7K1AdKjbuMsmPmPGDLaKL38M5HYwqxW9RKW49n",
            "predicate": "UN.CEFACT.Trade.CertificateOfOrigin.created"
        }
        response = self.client.post(url_for('views.incoming_message'), json=message_data)
        assert response.status_code == 200
        assert 'id' in response.json
        assert self.channel_repo.get_message(response.json['id'])
