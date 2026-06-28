# backend\services\chat\pipeline\chat_dto.py

from dataclasses import dataclass

@dataclass
class ChatMessageDTO:
    user: str
    content: str
    badges: list
    color: str
    msg_id: str
    sender_id: int
    is_cancelled: bool = False