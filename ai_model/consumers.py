from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import ChatSession
import json

class ChatConsumer(AsyncWebsocketConsumer):

    @database_sync_to_async
    def get_session_messages(self, session_id, user):
       
        session = ChatSession.objects.filter(id=session_id, users=user).prefetch_related("messages").first()
        if not session:
            return []  

        messages = session.messages.all().order_by("created_at")
        return [
            {
                "id": msg.id,
                "sender": msg.sender,
                "message": msg.content,
                "timestamp": msg.created_at.isoformat(),
            }
            for msg in messages
        ]

    async def connect(self):
        self.user = self.scope['user']
        if not self.user.is_authenticated:
            await self.close()
            return

        self.session_id = self.scope['url_route']['kwargs']['session_id']
        self.room_group_name = f'chat_{self.session_id}'

        # Add user to group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

        
        messages = await self.get_session_messages(self.session_id, self.user)
        await self.send(text_data=json.dumps({
            "type": "previous_messages",
            "messages": messages
        }))

    
    # async def receive(self, text_data = None, bytes_data = None):
        

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
