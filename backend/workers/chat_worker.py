# backend\workers\chat_worker.py

from PySide6.QtCore import QThread, Signal
from backend.providers.kick.kick_client import KickAPIClient
from backend.providers.kick.kick_websocket import ChatSocketManager

class ChatWorker(QThread):
    message_received = Signal(str, str, list, str, str, int) 
    error_occurred = Signal(str)        
    connection_success = Signal(dict)   
    
    def __init__(self, i18n, api_client: KickAPIClient, cluster: str, key: str, parent=None):
        super().__init__(parent)
        self.i18n = i18n
        self.setObjectName("Worker_Chat_Socket")
        self.api_client = api_client 
        self.cluster = cluster
        self.key = key
        self.chat_manager = ChatSocketManager(cluster, key)
        self._is_stopped = False

    def run(self):
        try:
            user_data = self.api_client.fetch_user_data()
            if self._is_stopped:
                return 

            room_id = user_data.get("room_id")
            if not room_id:
                raise ValueError(self.i18n.get("main.workers.chat.error_room_id"))

            self.connection_success.emit(user_data)

            while not self._is_stopped:
                self.chat_manager.start_socket(room_id, on_message=self._dispatch_message)
                if not self._is_stopped:
                    self.msleep(5000)

        except Exception as e:
            if not self._is_stopped:
                self.error_occurred.emit(str(e))

    def _dispatch_message(self, user: str, msg: str, badges: list, color: str, msg_id: str, sender_id: int):
        if not self._is_stopped:
            self.message_received.emit(user, msg, badges, color, msg_id, sender_id)

    def stop(self):
        self._is_stopped = True
        self.chat_manager.stop_socket()