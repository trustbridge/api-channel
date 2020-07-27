import pytest
import responses
from flask import url_for


@pytest.mark.usefixtures("client_class", "mocked_responses")
class TestPostMessage:
    message_data = {
        "sender": "AU",
        "receiver": "CN",
        "subject": "AU.abn0000000000.XXXX-XXXXX-XXXXX-XXXXXX",
        "obj": "QmQtYtUS7K1AdKjbuMsmPmPGDLaKL38M5HYwqxW9RKW49n",
        "predicate": "UN.CEFACT.Trade.CertificateOfOrigin.created"
    }

    def test_post_message__when_foreign_responded_ok__should_return_delivered(self):
        self.mocked_responses.add(
            responses.POST,
            'http://foreign-api-channel/incoming/messages',
            json=self.message_data
        )
        response = self.client.post(url_for('views.post_message'), json=self.message_data)
        assert response.status_code == 200
        assert response.json == {'status': 'delivered'}

    def test_post_message__when_foreign_responded_ok__should_return_rejected(self):
        self.mocked_responses.add(
            responses.POST,
            'http://foreign-api-channel/incoming/messages',
            json=self.message_data,
            status=400,
        )
        response = self.client.post(url_for('views.post_message'), json=self.message_data)
        assert response.status_code == 200
        assert response.json == {'status': 'rejected'}


@pytest.mark.usefixtures("client_class")
class TestGetMessage:
    def test_get_message__should_return_empty_dict(self):
        response = self.client.get(url_for('views.get_message', id=100))
        assert response.status_code == 200
        assert response.json == {}

    def test_get_message_status__should_return_delivered(self):
        url = url_for('views.get_message', id=100)
        response = self.client.get(f'{url}?fields=status')
        assert response.status_code == 200
        assert response.json == {'status': 'delivered'}
