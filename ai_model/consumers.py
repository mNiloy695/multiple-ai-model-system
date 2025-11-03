from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import ChatSession,ChatMessage
import json
from django.contrib.auth import get_user_model
from jwt import decode as jwt_decode
from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.tokens import UntypedToken
import google.generativeai as genai
User = get_user_model()

def gemini_response(message,model_id,api_key):
   API_KEY = api_key 
   genai.configure(api_key=API_KEY)
   #load the model using model_id
   model = genai.GenerativeModel(model_id)
   response = model.generate_content(message)
   return response.text




   
   



class ChatConsumer(AsyncWebsocketConsumer):
    
    @database_sync_to_async
    def get_session_messages(self, session_id, user):
       
        session = ChatSession.objects.filter(id=session_id, user=user).prefetch_related("messages").first()
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
    @database_sync_to_async
    def get_session_data(self, session_id, user):
      try:
        session = ChatSession.objects.select_related("user").get(id=session_id, user=user)
        return {
            "id": session.id,
            "user": session.user.id,
            "model": getattr(session, "model", None),  # only if model field exists
            "created_at": session.created_at.isoformat(),
            "updated_at": session.updated_at.isoformat() if hasattr(session, "updated_at") else None,
            "total_messages": session.messages.count(),
        }
      except ChatSession.DoesNotExist:
        return None

    
    @database_sync_to_async
    def save_message(self, session_id, user,sender,content):
        print(user)
        try:
           session = ChatSession.objects.get(id=session_id, user=user)
        except ChatSession.DoesNotExist as e:
           print("session not found")
           raise e
        print(user)
        if not content.strip():
               return
        msg = ChatMessage.objects.create(
            session=session,
            sender=sender, 
            content=content
        )
       
        return {
            "id": msg.id,
            "sender": msg.sender,
            "content": msg.content,
            "timestamp": msg.created_at.isoformat()
        }
    
    async def get_user_from_token(self):
        query_string = self.scope['query_string'].decode()
        token = None
        for part in query_string.split("&"):
           if part.startswith("token="):
             token = part.split("=")[1]

        if not token:
          return AnonymousUser()
 
        try:
          decoded = jwt_decode(token, settings.SECRET_KEY, algorithms=["HS256"])
          user_id = decoded.get("user_id")
          user = await database_sync_to_async(User.objects.get)(id=user_id)
          return user
        except Exception:
          return AnonymousUser()

    async def connect(self):
        print("i am in the connect function")
        self.user = await self.get_user_from_token()
        print(self.user)
        if not self.user.is_authenticated:
            await self.close()
            print("not authenticated")
            return

        self.session_id = self.scope['url_route']['kwargs']['session_id']
        # if self.session_id:
        #    session = await database_sync_to_async(ChatSession.objects.filter(id=self.session_id, user=self.user).first)()
        #    if session:
        #       self.session = session
        #    else:
        #       self.session = await database_sync_to_async(ChatSession.objects.create)(user=self.user, model=None)
        # else:
        
        #     self.session = await database_sync_to_async(ChatSession.objects.create)(user=self.user, model=None)
    

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

    
    async def receive(self, text_data=None, bytes_data=None):
      if not text_data:
        
         return

      try:
        data = json.loads(text_data)
      except json.JSONDecodeError:
        
        await self.send(text_data=json.dumps({
            "type": "error",
            "message": "Invalid JSON format"
        }))
        return

      message_content = data.get("message")
     
      saved_message = await self.save_message(
        session_id=self.session_id,
        user=self.user,
        sender="user",
        content=message_content
     )
      
      await self.send(text_data=json.dumps({
        "type": "new_message",
        "message": saved_message
    }))
    
      session_data=await self.get_session_data(session_id=self.session_id,user=self.user)

      if session_data:
         model=session_data.model
         if model:
            provider=model.provider
            model_id=model.model_id
            api_key=model.api_key

            if provider.lower()=='google':
               

         
     

        

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
