import json
import html
from channels.generic.websocket import AsyncWebsocketConsumer

class ChatConsumer(AsyncWebsocketConsumer):

   async def connect(self):
    self.room_name = self.scope["url_route"]["kwargs"]["room_name"]
    self.room_group_name = f"chat_{self.room_name}"

    await self.channel_layer.group_add(
        self.room_group_name,
        self.channel_name
    )

    await self.accept()
    print(f"Connessione accettata in stanza: {self.room_name}")
    await self.send(text_data=json.dumps({"msg": "SERVER: Connesso alla stanza!"}))

async def receive(self, text_data):
        print(f"Messaggio ricevuto: {text_data}")
        try:
            data = json.loads(text_data)
            username = html.escape(data.get("user", "anonimo"))
            message = html.escape(data.get("msg", ""))
            print(f"Inviando messaggio a gruppo {self.room_group_name}: {username}: {message}")

            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "chatroom_message",
                    "user": username,
                    "msg": message,
                }
            )
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({"msg": "SERVER: Messaggio non valido!"}))

async def chatroom_message(self, event):
        print(f"Broadcast messaggio ricevuto: {event}")
        await self.send(text_data=json.dumps({
            "user": event["user"],
            "msg": event["msg"]
        }))
