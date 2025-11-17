from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import ChatSession, ChatMessage
import json
from django.contrib.auth import get_user_model
from jwt import decode as jwt_decode
from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from django.contrib.auth import get_user_model
import base64,requests

User = get_user_model()


from .leonardo import leonardo_response
from .openai_func  import gpt_response
from .google_func import gemini_response
from .wavespeedai import wavespeed_ai_call
from PIL import Image
from io import BytesIO




class ChatConsumer(AsyncWebsocketConsumer):
    # max_message_size = 10 * 1024 * 1024 
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
                 "summary": getattr(session, "summary", ""),
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
        await self.send(text_data=json.dumps({"type": "previous_messages", "messages": messages},ensure_ascii=False))

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
        height=data.get('height')
        width=data.get('width')
        num_images=data.get('num_images')

        
        saved_message = await self.save_message(
            self.session_id, self.user, "user", content=message_content, images=user_images
        )
        if saved_message:
            await self.send(text_data=json.dumps({"type": "new_message", "message": saved_message}))

      
        session_data = await self.get_session_data(self.session_id, self.user)
        if not session_data or not session_data.get("model"):
            await self.send(text_data=json.dumps({"text": "no available session found"}))
            await self.close(1000)
            return 

        model = session_data.get("model")
        provider = getattr(model, "provider", "").lower()

        if provider == "google":
            model_id = getattr(model, "model_id", None)
            api_key = getattr(model, "api_key", None)
            if model_id and api_key:
                try:
                    ai_response = await database_sync_to_async(gemini_response)(
                        message_content, model_id, api_key, self.user.id,user_images,summary=session_data.get("summary"),num_images=num_images
                    )
                    if ai_response:
                        saved_ai_message = await self.save_message(
                            self.session_id,
                            self.user,
                            "ai",
                            content = ai_response.get("text") or ai_response.get("content") or ai_response.get("error") or "",

                            images=ai_response.get("images", [])
                        )
                        if saved_ai_message:
                            await self.send(text_data=json.dumps({"type": "new_message", "message": saved_ai_message}))
                except Exception as e:
                    await self.send(text_data=json.dumps({"type": "error", "message": f"AI error: {str(e)}"},ensure_ascii=False))
        elif provider=="openai":
            model_id = getattr(model, "model_id", None)
            api_key = getattr(model, "api_key", None)
            
            if model_id and api_key:
                try:
                    ai_response = await database_sync_to_async(gpt_response)(
                        message_content, model_id, api_key, self.user.id,user_images,height,width,summary=session_data.get("summary"),num_images=num_images
                    )

                    
                    if ai_response:
                        image_blocks=[]
                        images=ai_response.get("images", [])
                        images = [img for img in images if img.startswith("http")]
                        # print(images)
                        # if images:
                        #     for img in images:
                        #         png_bytes = base64.b64decode(img)
                        #         image = Image.open(BytesIO(png_bytes))
                        #         buffered = BytesIO()
                        #         image.save(buffered, format="WEBP", quality=80)
                        #         webp_b64 = base64.b64encode(buffered.getvalue()).decode()
                        #         image_blocks.append(webp_b64)
                        saved_ai_message = await self.save_message(
                            self.session_id,
                            self.user,
                            "ai",
                            content = ai_response.get("text") or ai_response.get("content") or ai_response.get("error") or "",

                            images=images
                        )
                        if saved_ai_message:
                            await self.send(text_data=json.dumps({"type": "new_message", "message": saved_ai_message},ensure_ascii=False))
                except Exception as e:
                    await self.send(text_data=json.dumps({"type": "error", "message": f"AI error: {str(e)}"}))
        


        elif provider=='leonardo':
            model_id = getattr(model, "model_id", None)
            api_key = getattr(model, "api_key", None)
            num_images=data.get("num_images",1)
            width=data.get("width",512)
            height=data.get("height",512)

            if model_id and api_key:
                # print("i am in the leonardo")
                try:
                    ai_response=await database_sync_to_async(leonardo_response)(
                        prompt=message_content,user_id=self.user.id,model_id=model_id,api_key=api_key,num_images=num_images,width=width,height=height,summary=session_data.get("summary")
                    )
                    if ai_response:
                        saved_ai_message = await self.save_message(
                            self.session_id,
                            self.user,
                            "ai",
                            content = ai_response.get("text") or ai_response.get("content") or ai_response.get("error") or "",
                            images=ai_response.get("images", [])
                        )
                        if saved_ai_message:
                            await self.send(text_data=json.dumps({"type": "new_message", "message": saved_ai_message}))
                except Exception as e:
                    await self.send(text_data=json.dumps({"type": "error", "message": f"AI error: {str(e)}"},ensure_ascii=False))



        elif provider=="wavespeedai":
            model_id=getattr(model,"model_id",None)
            api_key=getattr(model,"model_id",None)
            width=data.get("width",1024)
            height=data.get('height',1024)
            num_images=data.get('num_images',1)
            strength=data.get("strength",0.8)
            num_inference_steps=data.get("num_inference_steps",28)
            seed=data.get('seed',-1)
            guidance_scale=data.get("guidance_scale",3.5)
            output_format=data.get("output_format","jpeg")


            if model_id and api_key:
                payload = {
                      "prompt":f"A futuristic city skyline at sunset",  # <-- your prompt here
                      "strength":int(strength),
                      "size": f"{height}*{width}",
                      "num_inference_steps":int(num_inference_steps),
                      "seed": int(seed),
                      "guidance_scale":float(guidance_scale),
                      "num_images":int(num_images),
                      "output_format":output_format,
                      "enable_base64_output": False,
                      "enable_sync_mode": False
    }
                try:
                    ai_response=await database_sync_to_async(wavespeed_ai_call)(
                        model_id=model_id,
                        api_key=api_key,
                        payload=payload,
                        user_id=self.user.id
                    )
                    if ai_response:
                        saved_ai_message = await self.save_message(
                            self.session_id,
                            self.user,
                            "ai",
                            content = ai_response.get("text") or ai_response.get("content") or ai_response.get("error") or "",
                            images=ai_response.get("images", [])
                        )
                except Exception as e:
                      await self.send(text_data=json.dumps({"type": "error", "message": f"AI error: {str(e)}"},ensure_ascii=False))


                
        else:
            await self.send(text_data=json.dumps({"type": "error", "message": f"Unsupported provider: {provider}"},ensure_ascii=False))

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name ,self.channel_name)
