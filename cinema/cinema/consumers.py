# chat/consumers.py
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from django.contrib.auth import get_user_model
from chat.models import ChatMessage
from asgiref.sync import sync_to_async

User = get_user_model()

class ChatConsumer(AsyncWebsocketConsumer):
     #La connessione è accettata se l'utente corrisponde al nome della stanza o e staff
     # In questo modo le chat live saranno private tra l'utente e i membri dello staff
    async def connect(self):           
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = f'chat_{self.room_name}'
        self.user = self.scope['user']

        if not self.user.is_authenticated:
            await self.close()
            return

        # Staff può entrare in qualsiasi stanza, utente solo nella propria
        if not self.user.is_staff and self.user.username != self.room_name:
            await self.close()
            return

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        print(f"Creata/utente connesso alla chat {self.room_group_name}")
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    # Alla ricezione i messaggi vengono salvati nel db
    async def receive(self, text_data):
        data = json.loads(text_data)
        sender = self.user
        message = data.get("msg")

        if sender.is_staff:
            # Se è staff, manda al proprietario della stanza (room_name)
            try:
                recipient = await sync_to_async(User.objects.get)(username=self.room_name)
            except User.DoesNotExist:
                return
        else:
            # Se è utente normale, manda al primo staff disponibile  (staff1)
            try:
                recipient = await sync_to_async(User.objects.filter(is_staff=True).first)()
                if not recipient:   #Non dovrebbe mai verificarsi
                    await self.send(text_data=json.dumps({"user": "Sistema", "msg": "Nessun operatore disponibile"}))
                    return
            except:
                return

        # Salva il messaggio nel DB
        await sync_to_async(ChatMessage.objects.create)(
            user=recipient,
            sender=sender,
            message=message
        )

        # Invia il messaggio a tutti nel gruppo
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "chat_message",
                "user": sender.username,
                "msg": message
            }
        )

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            "user": event["user"],
            "msg": event["msg"]
        }))



