# frontend/workers/chat_worker.py

from PySide6.QtCore import QThread, Signal
from backend.kick_api_client import KickAPIClient
from backend.kick_websocket import ChatSocketManager

class ChatWorker(QThread):
    message_received = Signal(str, str) 
    error_occurred = Signal(str)        
    connection_success = Signal(dict)   
    
    def __init__(self, api_client: KickAPIClient, cluster: str, key: str, parent=None):
        super().__init__(parent)
        self.setObjectName("Worker_Chat_Socket")
        self.api_client = api_client 
        self.cluster = cluster
        self.key = key
        self.chat_manager = None

    def run(self):
        try:
            user_data = self.api_client.fetch_user_data()
            self.connection_success.emit(user_data)
            room_id = user_data.get("room_id")
            if not room_id:
                raise ValueError("No se pudo obtener el ID de la sala desde la API.")
                
            self.chat_manager = ChatSocketManager(self.cluster, self.key)

            def on_msg(user: str, msg: str):
                self.message_received.emit(user, msg)

            self.chat_manager.start_socket(room_id, on_message=on_msg)
        except Exception as e:
            self.error_occurred.emit(str(e))

    def stop(self):
        if self.chat_manager:
            self.chat_manager.stop_socket()