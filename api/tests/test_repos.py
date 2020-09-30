import pytest

from api.models import Message


class TestChannelRepo:
    @pytest.fixture(autouse=True)
    def message(self, clean_channel_repo):
        self.message = Message(message={"receiver": "AU"})
        self.repo = clean_channel_repo

    def test_save_message__for_new_message__should_save_with_new_id(self):
        message = self.repo.save_message(self.message)
        assert message.id

    def test_save_message__for_existing_id__should_use_it(self):
        self.message.id = '1234'
        message = self.repo.save_message(self.message)
        assert message.id == '1234'

    def test_get_message__when_exist__should_return_message(self):
        message = self.repo.save_message(self.message)
        received_message = self.repo.get_message(message_id=message.id)
        assert received_message == message

    def test_get_message__when_not_exist__should_return_none(self):
        message = self.repo.get_message(message_id='id')
        assert not message


class TestChannelQueueRepo:
    @pytest.fixture(autouse=True)
    def setup(self, clean_channel_queue_repo):
        self.repo = clean_channel_queue_repo

    def test_repo_enqueue__should_post_job_into_queue(self):
        self.repo.enqueue('message-id', 1)
        job = self.repo.get_job()
        assert job
        job_id, payload = job
        assert payload['message_id'] == 'message-id'
        assert payload['retry'] == 1
