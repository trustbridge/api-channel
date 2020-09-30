import enum
from dataclasses import dataclass
from dataclasses_json import dataclass_json


class MessageStatus(str, enum.Enum):
    RECEIVED = 'received'
    DELIVERED = 'delivered'
    CONFIRMED = 'confirmed'
    REVOKED = 'revoked'
    UNDELIVERABLE = 'undeliverable'


@dataclass_json
@dataclass
class Message:
    message: dict
    id: str = None
    status: MessageStatus = MessageStatus.RECEIVED
