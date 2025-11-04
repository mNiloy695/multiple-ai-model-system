from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import ChatSession, ChatMessage
import json
from django.contrib.auth import get_user_model
from jwt import decode as jwt_decode
from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from google import genai
from accounts.models import CreditAccount

User = get_user_model()


def gemini_response(message, model_id, api_key, user_id):
    """
    Sends a message to Google Gemini and returns a response.
    - Detects if model is text or image.
    - Deducts credits for prompt + AI response.
    Returns dict {"text": str, "images": [url1, url2, ...]}
    """
    client = genai.Client(api_key=api_key)

    user = User.objects.filter(id=user_id).first()
    if not user:
        return {"error": "User not found.", "images": []}

    credit_account = CreditAccount.objects.get(user=user)
    prompt_words = len(message.split())
    if credit_account.credits < prompt_words:
        return {"error": "Insufficient credits.", "images": []}

    credit_account.credits -= prompt_words
    credit_account.save()

    text = ""
    images = []

    try:
        
        if "image" in model_id.lower() or "bison" in model_id.lower():
            
            response = client.models.generate_image(model=model_id, prompt=message, size="1024x1024")
            try:
                images.append(response.candidates[0].content[0].image_uri)
                text = "Generated image(s)"
            except Exception:
                text = "Image generated but failed to fetch URL."
        else:
          
            try:
                response = client.models.generate_chat(
                    model=model_id,
                    messages=[{"author": "user", "content": message}]
                )
                text = response.candidates[0].content.parts[0].text
            except Exception:
                response = client.models.generate_content(model=model_id, contents=message)
                text = getattr(response, "text", str(response))

        # Deduct AI response credits for text only
        response_words = len(text.split())
        if credit_account.credits < response_words:
            return {"error": "Insufficient credits for AI response.", "images": images}
        credit_account.credits -= response_words
        credit_account.save()

        return {"text": text, "images": images}

    except Exception as e:
        return {"error": f"Gemini request failed: {str(e)}", "images": []}



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
                "content": msg.content,
                "images": msg.images,
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
                "model": getattr(session, "model", None),
                "created_at": session.created_at.isoformat(),
                "updated_at": session.updated_at.isoformat() if hasattr(session, "updated_at") else None,
                "total_messages": session.messages.count(),
            }
        except ChatSession.DoesNotExist:
            return None

    @database_sync_to_async
    def save_message(self, session_id, user, sender, content=None, images=None):
        if not content and not images:
            return None

        try:
            session = ChatSession.objects.get(id=session_id, user=user)
        except ChatSession.DoesNotExist:
            return None

        msg = ChatMessage.objects.create(
            session=session,
            sender=sender,
            content=content or "",
            images=images or []
        )

        return {
            "id": msg.id,
            "sender": msg.sender,
            "content": msg.content,
            "images": msg.images,
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
        self.user = await self.get_user_from_token()
        if not self.user.is_authenticated:
            await self.close()
            return

        self.session_id = self.scope['url_route']['kwargs']['session_id']
        self.room_group_name = f'chat_{self.session_id}'

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

        messages = await self.get_session_messages(self.session_id, self.user)
        await self.send(text_data=json.dumps({"type": "previous_messages", "messages": messages}))

    async def receive(self, text_data=None, bytes_data=None):
        if not text_data:
            return

        try:
            data = json.loads(text_data)
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({"type": "error", "message": "Invalid JSON format"}))
            return

        message_content = data.get("message", "")
        user_images = data.get("images", [])

        # Save user message with multiple images
        saved_message = await self.save_message(
            self.session_id, self.user, "user", content=message_content, images=user_images
        )
        if saved_message:
            await self.send(text_data=json.dumps({"type": "new_message", "message": saved_message}))

        # AI response logic
        session_data = await self.get_session_data(self.session_id, self.user)
        if not session_data or not session_data.get("model"):
            return

        model = session_data.get("model")
        provider = getattr(model, "provider", "").lower()

        if provider == "google":
            model_id = getattr(model, "model_id", None)
            api_key = getattr(model, "api_key", None)
            if model_id and api_key:
                try:
                    ai_response = await database_sync_to_async(gemini_response)(
                        message_content, model_id, api_key, self.user.id
                    )
                    if ai_response:
                        saved_ai_message = await self.save_message(
                            self.session_id,
                            self.user,
                            "ai",
                            content=ai_response.get("text", ""),
                            images=ai_response.get("images", [])
                        )
                        if saved_ai_message:
                            await self.send(text_data=json.dumps({"type": "new_message", "message": saved_ai_message}))
                except Exception as e:
                    await self.send(text_data=json.dumps({"type": "error", "message": f"AI error: {str(e)}"}))
        else:
            await self.send(text_data=json.dumps({"type": "error", "message": f"Unsupported provider: {provider}"}))

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)
