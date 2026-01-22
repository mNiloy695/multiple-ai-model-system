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
from .text_to_video.text_to_video import text_to_video_generation
from .image_tool.image_tool import image_tool_via_wavespeedai

User = get_user_model()
from django.db.models import F

from .leonardo import leonardo_response
from .openai_func  import gpt_response
from .google_func import gemini_response
from .wavespeedai import wavespeed_ai_call
from PIL import Image
from io import BytesIO
from .image_to_url_save import download_and_store_webp
from .fal_ai import call_fal_ai
from asgiref.sync import sync_to_async
from django.db import transaction
from .image_upscaler.image_upscaler import image_upscaler_wavespeed_ai
from .image_edit.image_edit import image_edit
from .image_to_3d.image_to_3d import image_to_3d
from .download_video.download_veo_video import generate_veo3_preview_video

def detect_media_easy(url):
    if not url or not isinstance(url, str):
        return "unknown"
        
    # Handle Base64 Data URIs
    if url.startswith("data:image/") or ";base64," in url:
        return "image"
        
    url_lower = url.lower()

    if url_lower.endswith((".jpg", ".jpeg", ".png", ".gif", ".webp")):
        return "image"

    if url_lower.endswith((".mp4", ".mov", ".avi", ".mkv", ".webm")):
        return "video"

    return "unknown"


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
    def decrement_api_limit(self, user_id):
        updated = User.objects.filter(
        id=user_id.id,
        api_limit__gt=0
    ).update(api_limit=F('api_limit') - 1)
        return updated  # 0 = limit exceeded

    @database_sync_to_async
    def get_remaining_credits(self, user):
        from accounts.models import CreditAccount
        # Use user_id for more robust querying across threads
        acc = CreditAccount.objects.filter(user_id=user.id).first()
        res = float(acc.credits) if acc else 0.0
        print(f"DEBUG: Fetched remaining credits for user {user.id}: {res}")
        return res

    async def send_json_with_credits(self, data):
        """Helper to send JSON response including current remaining credits."""
        data["remaining_credits"] = await self.get_remaining_credits(self.user)
        await self.send(text_data=json.dumps(data, ensure_ascii=False))
    

    @database_sync_to_async
    def save_message(self, session_id, user, sender, content=None, images=None):
        if not content and not images:
            return None

        try:
            session = ChatSession.objects.get(id=int(session_id), user=user)
        except ChatSession.DoesNotExist:
            print(f"DEBUG: save_message failed - ChatSession {session_id} not found for user {user.id}")
            return None
        except Exception as e:
            print(f"DEBUG: save_message unexpected error: {str(e)}")
            return None

        msg = ChatMessage.objects.create(
            session=session,
            sender=sender,
            content=content or "",
            images=images or []
        )
        print(f"DEBUG: Successfully saved {sender} message to session {session_id}")

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
        await self.send_json_with_credits({"type": "previous_messages", "messages": messages})

    async def receive(self, text_data=None, bytes_data=None):
        if not text_data:
            return

        try:
            data = json.loads(text_data)
        except json.JSONDecodeError:
            await self.send_json_with_credits({"type": "error", "message": "Invalid JSON format."})
            return

        fresh_user=await database_sync_to_async(User.objects.get)(id=self.user.id)
        self.user=fresh_user
        
        if fresh_user.api_limit<=0:
            await self.send_json_with_credits({
                "type": "limit exceed",
                "message": "You have exceeded your daily limit. Please watch ads or buy a subscription for more requests."
            })
            return 
        



        message_content = data.get("message", "")
        user_images = data.get("images", [])


        height=data.get('height')
        width=data.get('width')
        num_images=data.get('num_images')
        duration=data.get('duration')

        #set word limit for free trail

        if not self.user.subscribed:
            message_content_words=message_content.split()
            if len(message_content_words)>400:
                message_content=str(message_content[:400])
        
        await self.decrement_api_limit(self.user)


        if user_images:
                if isinstance(user_images,str):
                  user_images=[user_images]
                detect_image_or_video=await sync_to_async(detect_media_easy)(user_images[0] if user_images else None)
                if detect_image_or_video =="unknown":
                    await self.send_json_with_credits({"type": "error", "message": "Unknown media link. Please select an image or video."})
                    return
                elif detect_image_or_video=="image":
                    images=await sync_to_async(download_and_store_webp)(image_urls=user_images)
                    # Support for passing stored links to AI if original was base64
                    processed_user_images = []
                    for i, original in enumerate(user_images):
                        if (original.startswith("data:image/") or ";base64," in original) and images[i]:
                            processed_user_images.append(images[i])
                        else:
                            processed_user_images.append(original)
                    user_images = processed_user_images
                    data["images"] = user_images # Update the data dict for subsequent model calls
                if detect_image_or_video =="video":
                    images=user_images
                images = [img for img in images if img]
                        
                saved_message = await self.save_message(
                            self.session_id,
                            self.user,
                            "user",
                            content = message_content,
                            images=images
                        )
                if saved_message:
                            await self.send_json_with_credits({"type": "new_message", "message": saved_message})
        else: 
            saved_message = await self.save_message(
            self.session_id, self.user, "user", content=message_content, images=user_images
              )
            if saved_message:
               await self.send_json_with_credits({"type": "new_message", "message": saved_message})
        

      
        session_data = await self.get_session_data(self.session_id, self.user)
        if not session_data or not session_data.get("model"):
            await self.send_json_with_credits({"text": "no available session found"})
            await self.close(1000)
            return 

        model = session_data.get("model")
        
        # Check for empty message specifically for chat models
        model_type = getattr(model, "model_type", None)
        if model_type == "chat" and not message_content and not user_images:
            await self.send_json_with_credits({"type": "error", "message": "Please type a message to receive assistance."})
            return

        provider = getattr(model, "provider", "").lower()

        if provider == "google":
            model_id = getattr(model, "model_id", None)
            api_key = getattr(model, "api_key", None)
            model_type=getattr(model,"model_type",None)
            if model_type:
                 model_type = model_type.strip()
            base_cost=getattr(model,"base_cost",0)
            if not base_cost or base_cost <= 0:
                base_cost = 500
            aspect_ratio=data.get("aspect_ratio",None)
            resolution=data.get("resolution",None)
        
            if not self.user.subscribed:
                await self.send(json.dumps({"type":"error","message":"Only free model is available for free users. Please upgrade/buy coins to access premium models."}))
                return

            if model_type=="text_to_video":
                try:
                    ai_response = await generate_veo3_preview_video(api_key=api_key, prompt=message_content, aspect_ratio=aspect_ratio, model_id=model_id, resolution=resolution,user_id=self.user.id,base_cost=base_cost)
                    

                    if ai_response:
                        print(ai_response,"--------------------")
                        saved_ai_message = await self.save_message(
                            self.session_id,
                            self.user,
                            "ai",
                            content = ai_response.get("text") or ai_response.get("content") or ai_response.get("error") or "",

                            images=ai_response.get("images", [])
                        )
                        if saved_ai_message:
                            await self.send_json_with_credits({"type": "new_message", "message": saved_ai_message})

                except Exception as e:
                    await self.send_json_with_credits({"type": "error", "message": f"Error: {str(e)}"})
                
            else:
                try:
                    
                    ai_response = await gemini_response(
                        message=message_content,
                        model_id=model_id, 
                        api_key=api_key, 
                        user_id=self.user.id,
                        images_data_list=user_images,
                        summary=session_data.get("summary",""),
                        num_images=num_images,
                        base_cost=base_cost,
                        model_type=model_type
                    )
                    if ai_response:
                        raw_images = ai_response.get("images", [])
                        final_images = []
                        if raw_images:
                            downloaded = await database_sync_to_async(download_and_store_webp)(image_urls=raw_images)
                            final_images = [img for img in downloaded if img]

                        saved_ai_message = await self.save_message(
                            self.session_id,
                            self.user,
                            "ai",
                            content = ai_response.get("text") or ai_response.get("content") or ai_response.get("error") or "",
                            images=final_images if final_images else raw_images if not any(img.startswith("data:") for img in raw_images) else []
                        )
                        if saved_ai_message:
                            await self.send_json_with_credits({"type": "new_message", "message": saved_ai_message})
                except Exception as e:
                    await self.send_json_with_credits({"type": "error", "message": f"Error: {str(e)}"})
        elif provider=="openai":
            model_id = getattr(model, "model_id", None)
            api_key = getattr(model, "api_key", None)
            num_images=data.get("num_images",1)
            height=data.get("height",512)
            width=data.get("width",512)
            duration=data.get("duration",'4')
            aspect_ratio=data.get("aspect_ratio",None)
            # fresh_user=await database_sync_to_async(User.objects.get)(id=self.user.id)
            # self.user=fresh_user
            # 1024x1024 (square) - 1536x1024 (landscape) - 1024x1536
            
            if not self.user.subscribed:
                await self.send(json.dumps({"type":"error","message":"Only free model is available for free users. Please upgrade to access premium models."}))
                return
            
            if model_id and api_key:

                try:
                    base_cost=getattr(model,"base_cost",0)
                    if not base_cost or base_cost <= 0:
                        base_cost = 500

                    seed = data.get("seed", -1)
                    if model_type=="text_to_video" or model_type=="image_to_video" or model_type=="text_or_image_to_video":
                        from .openai_video.openai_video import call_openai_video_model
                        ai_response = await call_openai_video_model(
                            model_id=model_id,
                            api_key=api_key,
                            user_id=self.user.id,
                            prompt=message_content,
                            duration=duration,
                            width=width,
                            height=height,
                            seed=seed,
                            base_cost=base_cost
                        )
                    else:
                        ai_response = await gpt_response(message=message_content,model_id=model_id,api_key=api_key,user_id=self.user.id,images_data_list=user_images,summary=session_data.get("summary"),num_images=num_images,base_cost=base_cost,duration=duration,height=height,width=width,aspect_ratio=aspect_ratio)

                    
                    if ai_response:

                        # Download and store images locally
                        raw_images = ai_response.get("images", [])
                        final_images = []
                        if raw_images:

                            # Use the existing download utility
                            downloaded = await database_sync_to_async(download_and_store_webp)(image_urls=raw_images)
                            final_images = [img for img in downloaded if img]

                        
                        resp_content = ai_response.get("text") or ai_response.get("content") or ai_response.get("error") or ""
                        
                        # Safety fallback if somehow both are empty
                        if not resp_content and not final_images and not raw_images:
                            resp_content = "The model generated an empty response. Please try again."

                        saved_ai_message = await self.save_message(
                            self.session_id,
                            self.user,
                            "ai",
                            content = resp_content,
                            images=final_images if final_images else raw_images if not any(img.startswith("data:") for img in raw_images) else []
                        )
                        if saved_ai_message:

                            await self.send_json_with_credits({"type": "new_message", "message": saved_ai_message})
                        else:

                            await self.send(text_data=json.dumps({"type": "error", "message": "Failed to save or process AI response."},ensure_ascii=False))
                except Exception as e:
                    print("error is occure ")
                    await self.send_json_with_credits({"type": "error", "message": f"Error: {str(e)}"})
        


        elif provider=='leonardo':
            if not self.user.subscribed:
                await self.send(json.dumps({"type":"error","message":"Only free model is available for free users. Please upgrade to access premium models."}))
                return
            model_id = getattr(model, "model_id", None)
            api_key = getattr(model, "api_key", None)
            num_images=data.get("num_images",1)
            width=data.get("width",512)
            height=data.get("height",512)
            # fresh_user=await database_sync_to_async(User.objects.get)(id=self.user.id)
            # self.user=fresh_user

            if model_id and api_key:
                # print("i am in the leonardo")
                try:
                    base_cost=getattr(model,"base_cost",0)
                    if not base_cost or base_cost <= 0:
                        base_cost = 500
                    ai_response=await database_sync_to_async(leonardo_response)(
                        prompt=message_content,user_id=self.user.id,model_id=model_id,api_key=api_key,num_images=num_images,width=width,height=height,summary=session_data.get("summary"),BASE_COST=base_cost
                    )
                    if ai_response:
                        print("DEBUG: Leonardo Response:", ai_response)
                        # Download and store images locally
                        raw_images = ai_response.get("images", [])
                        final_images = []
                        if raw_images:
                            downloaded = await database_sync_to_async(download_and_store_webp)(image_urls=raw_images)
                            final_images = [img for img in downloaded if img]

                        saved_ai_message = await self.save_message(
                            self.session_id,
                            self.user,
                            "ai",
                            content = ai_response.get("text") or ai_response.get("content") or ai_response.get("error") or "",
                            images=final_images if final_images else raw_images if not any(img.startswith("data:") for img in raw_images) else []
                        )
                        if saved_ai_message:
                            await self.send_json_with_credits({"type": "new_message", "message": saved_ai_message})
                except Exception as e:
                    await self.send_json_with_credits({"type": "error", "message": f"Error: {str(e)}"})



        elif provider=="wavespeedai":
            if not self.user.subscribed:
                await self.send(json.dumps({"type":"error","message":"Only free model is available for free users. Please upgrade to access premium models."}))
                return
            model_id = getattr(model, "model_id", None)
            api_key = getattr(model, "api_key", None)
            width = data.get("width", 1024)
            height = data.get("height", 1024)
            num_images = data.get("num_images", 1)
            num_inference_steps = data.get("num_inference_steps", 45)  # higher for quality
            guidance_scale = data.get("guidance_scale", 7.5)           # follow prompt better
            seed = data.get("seed", 42)                                # fixed seed for consistency
            output_format = data.get("output_format", "jpeg")
            prompt = data.get("message")
            image=data.get("images",None)
            resolution=data.get("resolution","1080p")
            generate_audio=data.get("generate_audio",False)
            aspect_ratio=data.get("aspect_ratio","1:1")
        
            print(image)




            if model_id and api_key:
                base_cost=getattr(model,"base_cost",0)
                if not base_cost or base_cost <= 0:
                    base_cost = 500
                model_type=getattr(model,"model_type",None)
                if model_type:
                     model_type = model_type.strip()
                print(model_type)
                
                #for chat model

                if model_type=="chat":
                   await self.send_json_with_credits({"type": "error", "message": f"This model does not support chat"})
                
                #image editor
              
                
                #text to image generation
                elif model_type=="text_to_image":
                  payload={
                        "enable_base64_output": False,
                        "enable_sync_mode": False,
                        "prompt":prompt,
                        "seed":-1,
                        "size": f"{height} * {width}" if height and width  else "1024*1024"
                    }
                                              
                  try:
                     
                    ai_response = await wavespeed_ai_call(
                        model_id=model_id,
                        api_key=api_key,
                        payload=payload,
                        user_id=self.user.id,
                        base_cost=base_cost
                    )
                    
                    if ai_response:
                        print("AI RESPONSE FROM WEAVESPEEDAI:", ai_response)
                        raw_images = ai_response.get("images", [])
                        final_images = []
                        if raw_images:
                            downloaded = await database_sync_to_async(download_and_store_webp)(image_urls=raw_images)
                            final_images = [img for img in downloaded if img]

                        saved_ai_message = await self.save_message(
                            self.session_id,
                            self.user,
                            "ai",
                            content = ai_response.get("text") or ai_response.get("content") or ai_response.get("error") or "",
                            images=final_images if final_images else raw_images if not any(img.startswith("data:") for img in raw_images) else []
                        )
                        if saved_ai_message:
                            await self.send_json_with_credits({"type": "new_message", "message": saved_ai_message})
                  except Exception as e:
                      await self.send_json_with_credits({"type": "error", "message": f"Error: {str(e)}"})
                
                #text to video generation
                elif model_type=="text_to_video":
                    try:
                        ai_response = await text_to_video_generation(
                            model_id=model_id,
                            prompt=prompt,
                            api_key=api_key,
                            duration=duration,
                            height=height,
                            width=width,
                            seed=seed,
                            resolution=resolution,
                            generate_audio=generate_audio,
                            base_cost=base_cost,
                            user_id=self.user.id
                        )
                        print("AI RESPONSE FROM WEAVESPEEDAI:",ai_response)

                        if ai_response:
                         # For Wavespeed video, ai_response is the URL string or dict with url
                         video_url = ai_response.get("url") if isinstance(ai_response, dict) else ai_response
                         saved_ai_message = await self.save_message(
                            self.session_id,
                            self.user,
                            "ai",
                            content = "Video generated successfully.",
                            images=[video_url]
                        )
                         if saved_ai_message:
                            await self.send_json_with_credits({"type": "new_message", "message": saved_ai_message})
                            
                    except Exception as e:
                        await self.send_json_with_credits({"type": "error", "message": f"Error: {str(e)}"})
                        return
                elif model_type=="image_tool":
                    if not image or len(image) == 0:
                        await self.send_json_with_credits({"type": "error", "message": "Image tool requires an image. Please upload an image first."})
                        return

                    print("images", image[0])
                    style=data.get("style","default")
                    target_language=data.get('target_language',"english")
                    target_resolution=data.get("target_resolution","4k")
                    # fresh_user=await database_sync_to_async(User.objects.get)(id=self.user.id)
                    # self.user=fresh_user
                    try:
                        ai_response=await database_sync_to_async(image_tool_via_wavespeedai)(
                            model_id=model_id,
                            api_key=api_key,
                            user_id=self.user.id,
                            prompt=prompt,
                            image_url=image[0] if image else None,
                            base_cost= base_cost,
                            style=style,
                            target_language=target_language,
                            target_resolution=target_resolution
                        )
                        print("AI RESPONSE FROM WEAVESPEEDAI:",ai_response)

                        if ai_response:
                            print("AI RESPONSE FROM WEAVESPEEDAI:", ai_response)
                            # ai_response here is likely a URL string
                            raw_images = [ai_response] if isinstance(ai_response, str) else ai_response.get("images", [])
                            final_images = []
                            if raw_images:
                                downloaded = await database_sync_to_async(download_and_store_webp)(image_urls=raw_images)
                                final_images = [img for img in downloaded if img]

                            saved_ai_message = await self.save_message(
                                self.session_id,
                                self.user,
                                "ai",
                                content = "Image processed successfully",
                                images=final_images if final_images else raw_images if not any(img.startswith("data:") for img in raw_images) else []
                            )
                            if saved_ai_message:
                                await self.send_json_with_credits({"type": "new_message", "message": saved_ai_message})
                    except Exception as e:
                        await self.send_json_with_credits({"type": "error", "message": f"Error: {str(e)}"})
                        return
                elif model_type=="video_upscaler":
                    if not image or len(image) == 0:
                        await self.send_json_with_credits({"type": "error", "message": "Video/Image upscaler requires an image. Please upload one first."})
                        return
                    try:
                        target_resolution=data.get("target_resolution","4k")
                        ai_response=await database_sync_to_async(image_upscaler_wavespeed_ai)(
                            model_id=model_id,
                            api_key=api_key,
                            user_id=self.user.id,
                            image_url=image[0] if image else None,
                            base_cost= base_cost,
                            target_resolution=target_resolution
                        )
                        print("AI RESPONSE FROM WEAVESPEEDAI:",ai_response)

                        if ai_response:
                            saved_ai_message=await self.save_message(
                                self.session_id,
                                self.user,
                                "ai",
                                "Image upscaled successfully",
                                images=[ai_response]
                            )
                            if saved_ai_message:
                                await self.send_json_with_credits({"type": "new_message", "message": saved_ai_message})
                    except Exception as e:
                        await self.send_json_with_credits({"type": "error", "message": f"Error: {str(e)}"})
                        return
                

                elif model_type=="image_editor":
                    if not image or len(image) == 0:
                        await self.send_json_with_credits({"type": "error", "message": "Image editor requires an image. Please upload one first."})
                        return
                    
                    try:
                        ai_response=await database_sync_to_async(image_edit)(
                            model_id=model_id,
                            api_key=api_key,
                            user_id=self.user.id,
                            images=image[0] if image else None,
                            base_cost=base_cost,
                            output_format=output_format,
                            prompt=prompt,
                            aspect_ratio=aspect_ratio

                        )
                        print("AI RESPONSE FROM WEAVESPEEDAI:",ai_response)

                        if ai_response:
                            saved_ai_message=await self.save_message(
                                self.session_id,
                                self.user,
                                "ai",
                                "Image edited successfully",
                                images=[ai_response]
                            )
                            if saved_ai_message:
                                await self.send_json_with_credits({"type": "new_message", "message": saved_ai_message})

                       

                    
                    except Exception as e:
                        await self.send_json_with_credits({"type": "error", "message": f"Error: {str(e)}"})
                        return
                elif model_type=="image_to_3d":
                    if not image or len(image) == 0:
                        await self.send_json_with_credits({"type": "error", "message": "Image to 3D tool requires an image. Please upload one first."})
                        return
                    try:
                        ai_response=await database_sync_to_async(image_to_3d)(
                            model_id=model_id,
                            user_id=self.user.id,
                            api_key=api_key,
                            images=image[0] if image else None,
                            base_cost=base_cost

                        )

                        if ai_response:
                            saved_ai_message=await self.save_message(
                                self.session_id,
                                self.user,
                                "ai",
                                "3d image succesfully genereated",
                                images=[ai_response]
                            )
                        if saved_ai_message:
                                await self.send_json_with_credits({"type": "new_message", "message": saved_ai_message})

                    except Exception as e:
                        await self.send_json_with_credits({"type": "error", "message": f"Error: {str(e)}"})
                        return
                
                elif model_type=="video_effect":
                    from .video_effect.video_effect import video_effect
                    resolution=data.get("resolution",480)
                    effect=data.get("effect",None)
                    duration=data.get("duration",5)
                    bgm=data.get("bgm",False)
                    template=data.get("template","sexy_devil")
                    sound_effect_switch=data.get("sound_effect_switch",False)

                
                        
                    try:
                        ai_response=await database_sync_to_async(video_effect)(
                        model_id=model_id,
                        user_id=self.user.id,
                        api_key=api_key,
                        images=image[0] if image else None,
                        base_cost=base_cost,
                        duration=duration,
                        effect=effect,
                        resolution=resolution,
                        bgm=bgm,
                        seed=seed,
                        template=template,
                        sound_effect_switch=sound_effect_switch,
                        )
                        if ai_response:
                           saved_ai_message=await self.save_message(
                                self.session_id,
                                self.user,
                                "ai",
                                "Video Generated successfully",
                                images=[ai_response]
                        )
                           if saved_ai_message:
                                await self.send_json_with_credits({"type": "new_message", "message": saved_ai_message})


                    except Exception as e:
                        await self.send_json_with_credits({"type": "error", "message": f"Error: {str(e)}"})
                        return
                elif model_type=="text_to_speech":
                    from .text_to_speech.text_to_speech import text_to_sound
                    bitrate=data.get("bitrate",None)
                    emotion=data.get("emotion",None)
                    english_normalization=data.get("english_normalization",False)
                    formate=data.get("format","mp3")
                    language_boost=data.get("language_boost","auto")
                    pitch=data.get("pitch",1)
                    sample_rate=data.get("sample_rate",None)
                    speed=data.get("speed",1)
                    voice_id=data.get("voice_id","Wise_Woman")
                    volume=data.get("volume",1)
                    channel=data.get("channel",None)

                    print("this is the prompt--------------------------------------",prompt)



                    try:
                        ai_response=await database_sync_to_async(text_to_sound)(model_id=model_id,api_key=api_key,user_id=self.user.id,base_cost=base_cost,bitrate=bitrate,emotion=emotion,english_normalization=english_normalization,formate=formate,prompt=prompt,language_boost=language_boost,pitch=pitch,sample_rate=sample_rate,speed=speed,voice_id=voice_id,volume=volume,channel=channel)
                        if ai_response:
                           saved_ai_message=await self.save_message(
                                self.session_id,
                                self.user,
                                "ai",
                                "Video Generated successfully",
                                images=[ai_response]
                        )
                           if saved_ai_message:
                                await self.send_json_with_credits({"type": "new_message", "message": saved_ai_message})


                    except Exception as e:
                        await self.send_json_with_credits({"type": "error", "message": f"Error: {str(e)}"})

                
                # elif model_type=="image_to_video":
                    
                #     payload={
                #     "image": image,
                #     "prompt": prompt,
                #     "duration": 5,
                #     "fps": 24,
                #     "resolution": "480p",
                #     "seed": -1
                # }
        
        elif provider=="deepseek":
            from .deepseek import call_deepseek_for_chat
            model_id=getattr(model,'model_id',None)
            api_key=getattr(model,"api_key",None)
            model_type=getattr(model,"model_type",None)
            if model_type:
                model_type = model_type.strip()
            base_cost=getattr(model,"base_cost",0)
            if not base_cost or base_cost <= 0:
                base_cost = 1

            ai_response=await database_sync_to_async(call_deepseek_for_chat)(
                user_id=self.user.id,
                model_id=model_id,
                api_key=api_key,
                base_cost=base_cost,
                message=message_content,
                summary=session_data.get("summary")
            )
            if ai_response:
                raw_images = ai_response.get("images", [])
                final_images = []
                if raw_images:
                    downloaded = await database_sync_to_async(download_and_store_webp)(image_urls=raw_images)
                    final_images = [img for img in downloaded if img]

                saved_ai_message = await self.save_message(
                            self.session_id,
                            self.user,
                            "ai",
                            content = ai_response.get("text") or ai_response.get("content") or ai_response.get("error") or "",
                            images=final_images if final_images else raw_images if not any(img.startswith("data:") for img in raw_images) else []
                 )
                if saved_ai_message:
                            await self.send_json_with_credits({"type": "new_message", "message": saved_ai_message})
                

        

        elif provider=="falai":
            if not self.user.subscribed:
                await self.send(json.dumps({"type":"error","message":"Only free model is available for free users. Please upgrade to access premium models."}))
                return
            model_id = getattr(model, "model_id", None)
            api_key = getattr(model, "api_key", None)
            num_images=data.get("num_images",1)
            size=data.get("size","512x512")
            steps=data.get("steps",50)
            cfg_scale=data.get("cfg_scale",7.0)
            seed=data.get("seed",6252023)
            # fresh_user=await database_sync_to_async(User.objects.get)(id=self.user.id)
            # self.user=fresh_user

            if model_id and api_key:
                try:
                    base_cost=getattr(model,"base_cost",0)
                    if not base_cost or base_cost <= 0:
                        base_cost = 500
                    ai_response = await database_sync_to_async(call_fal_ai)(
                        api_key, message_content,model_id,self.user.id,num_images,base_cost,seed,steps,cfg_scale,size
                    )
                    if ai_response:
                        raw_images = ai_response.get("images", [])
                        final_images = []
                        if raw_images:
                            downloaded = await database_sync_to_async(download_and_store_webp)(image_urls=raw_images)
                            final_images = [img for img in downloaded if img]

                        saved_ai_message = await self.save_message(
                            self.session_id,
                            self.user,
                            "ai",
                            content = ai_response.get("text") or ai_response.get("content") or ai_response.get("error") or "",
                            images=final_images if final_images else raw_images if not any(img.startswith("data:") for img in raw_images) else []
                        )
                        if saved_ai_message:
                            await self.send_json_with_credits({"type": "new_message", "message": saved_ai_message})
                except Exception as e:
                    await self.send_json_with_credits({"type": "error", "message": f"Error: {str(e)}"})        
        else:
            await self.send_json_with_credits({"type": "error", "message": f"Unsupported provider: {provider}"})
      
    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name ,self.channel_name)
