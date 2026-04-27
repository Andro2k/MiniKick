import json, websocket, re, cloudscraper, requests

class ChatManager:
    def __init__(self, token, cluster, key):
        self.token = token
        self.cluster = cluster
        self.key = key

    def get_user_data(self):
        # Obtiene username y chatroomid
        user_resp = requests.get("https://api.kick.com/public/v1/users", 
                                 headers={"Authorization": f"Bearer {self.token}"}).json()
        username = user_resp.get("data", [user_resp])[0].get("name")
        
        scraper = cloudscraper.create_scraper()
        room_data = scraper.get(f"https://kick.com/api/v1/channels/{username}").json()
        return username, room_data.get("chatroom", {}).get("id")

    def clean_text(self, text):
        text = re.sub(r'http[s]?://\S+|www\.\S+', '', text) # Links
        text = re.sub(r'\[emote:.*?\]', '', text) # Emotes
        return text.strip()

    def start_socket(self, room_id, on_msg_callback):
        url = f"wss://ws-{self.cluster}.pusher.com/app/{self.key}?protocol=7&client=js&version=7.6.0"
        
        def on_message(ws, message):
            data = json.loads(message)
            if data.get("event") == "pusher:connection_established":
                ws.send(json.dumps({"event": "pusher:subscribe", "data": {"channel": f"chatrooms.{room_id}.v2"}}))
            elif data.get("event") == "App\\Events\\ChatMessageEvent":
                c = json.loads(data.get("data", "{}"))
                on_msg_callback(c.get("sender", {}).get("username"), self.clean_text(c.get("content", "")))
            elif data.get("event") == "pusher:ping":
                ws.send(json.dumps({"event": "pusher:pong"}))

        ws = websocket.WebSocketApp(url, on_message=on_message)
        ws.run_forever()