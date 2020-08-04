import enum
from dataclasses import dataclass

from marshmallow import Schema, post_load, fields
from marshmallow_enum import EnumField


class MessageStatus(enum.Enum):
    RECEIVED = 'received'
    DELIVERED = 'delivered'
    CONFIRMED = 'confirmed'
    REVOKED = 'revoked'
    UNDELIVERABLE = 'undeliverable'


@dataclass
class Message:
    payload: dict
    id: str = None
    status: MessageStatus = MessageStatus.RECEIVED


class MessageSchema(Schema):
    id = fields.UUID()
    status = EnumField(MessageStatus, by_value=True)
    payload = fields.Dict()

    @post_load
    def make_message(self, data, **kwargs):
        return Message(**data)
