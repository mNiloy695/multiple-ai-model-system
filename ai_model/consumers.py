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
    url = url.lower()

    if url.endswith((".jpg", ".jpeg", ".png", ".gif", ".webp")):
        return "image"

    if url.endswith((".mp4", ".mov", ".avi", ".mkv", ".webm")):
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
   

    # @database_sync_to_async  
    # def decrement_api_limit(self, user):
    #    with transaction.atomic():
    #      user.api_limit -= 1
    #      user.save()

    @database_sync_to_async
    def decrement_api_limit(self, user_id):
        updated = User.objects.filter(
        id=user_id.id,
        api_limit__gt=0
    ).update(api_limit=F('api_limit') - 1)
        return updated  # 0 = limit exceeded

    

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
            await self.send(text_data=json.dumps({"type": "error", "message": "Invalid JSON format"},ensure_ascii=False))
            return
        fresh_user=await database_sync_to_async(User.objects.get)(id=self.user.id)
        
        if fresh_user.api_limit<=0:
            await self.send(text_data=json.dumps({"type":"limit exceed","message":"You exceed today limit watch ads or buy subscription for get more request"},ensure_ascii=False))
            return 
        

        # self.decrement_api_limit(self.user)
        
     


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
        
        fresh_user=await database_sync_to_async(User.objects.get)(id=self.user.id)
        self.user=fresh_user
        await self.decrement_api_limit(self.user)
        # if ai_response:
        #        await self.decrement_api_limit(self.user)


        if user_images:
                if isinstance(user_images,str):
                  user_images=[user_images]
                detect_image_or_video=await sync_to_async(detect_media_easy)(user_images[0] if user_images else None)
                if detect_image_or_video =="unknown":
                    await self.send(json.dumps({"error":"unknown link select image or video"}))
                    return
                elif detect_image_or_video=="image":
                    images=await sync_to_async(download_and_store_webp)(image_urls=user_images)
                if detect_image_or_video =="video":
                    images=user_images
                images = [img for img in images]
                        
                saved_message = await self.save_message(
                            self.session_id,
                            self.user,
                            "user",
                            content = message_content,

                            images=images
                        )
                if saved_message:
                            await self.send(text_data=json.dumps({"type": "new_message", "message": saved_message},ensure_ascii=False))
        else: 
            saved_message = await self.save_message(
            self.session_id, self.user, "user", content=message_content, images=user_images
              )
            if saved_message:
               await self.send(text_data=json.dumps({"type": "new_message", "message": saved_message},ensure_ascii=False))
        

      
        session_data = await self.get_session_data(self.session_id, self.user)
        if not session_data or not session_data.get("model"):
            await self.send(text_data=json.dumps({"text": "no available session found"},ensure_ascii=False))
            await self.close(1000)
            return 

        model = session_data.get("model")
        provider = getattr(model, "provider", "").lower()

        if provider == "google":
            fresh_user=await database_sync_to_async(User.objects.get)(id=self.user.id)
            self.user=fresh_user
            model_id = getattr(model, "model_id", None)
            api_key = getattr(model, "api_key", None)
            model_type=getattr(model,"model_type",None)
            base_cost=getattr(model,"base_cost",500)
            aspect_ratio=data.get("aspect_ratio",None)
            resolution=data.get("resolution",None)
        
            if model_type=="text_to_video":
                try:
                    ai_response=await database_sync_to_async(generate_veo3_preview_video)(api_key=api_key, prompt=message_content, aspect_ratio=aspect_ratio, model_id=model_id, resolution=resolution,user_id=self.user.id,base_cost=base_cost)
                    

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
                            await self.send(text_data=json.dumps({"type": "new_message", "message": saved_ai_message},ensure_ascii=False))

                except Exception as e:
                    await self.send(text_data=json.dumps({"type": "error", "message": f"AI error: {str(e)}"},ensure_ascii=False))
                
            else:
                try:
                    
                    ai_response = await database_sync_to_async(gemini_response)(
                        message_content, model_id, api_key, self.user.id,user_images,summary=session_data.get("summary",""),num_images=num_images,base_cost=base_cost,model_type=model_type
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
                            await self.send(text_data=json.dumps({"type": "new_message", "message": saved_ai_message},ensure_ascii=False))
                except Exception as e:
                    await self.send(text_data=json.dumps({"type": "error", "message": f"AI error: {str(e)}"},ensure_ascii=False))
        elif provider=="openai":
            model_id = getattr(model, "model_id", None)
            api_key = getattr(model, "api_key", None)
            num_images=data.get("num_images",1)
            height=data.get("height",512)
            width=data.get("width",512)
            duration=data.get("duration",4)
            aspect_ratio=data.get("aspect_ratio",None)
            # fresh_user=await database_sync_to_async(User.objects.get)(id=self.user.id)
            # self.user=fresh_user
            # 1024x1024 (square) - 1536x1024 (landscape) - 1024x1536
            

            if model_id and api_key:
                try:
                    base_cost=getattr(model,"base_cost",500)
                    ai_response = await database_sync_to_async(gpt_response)(message=message_content,model_id=model_id,api_key=api_key,user_id=self.user.id,images_data_list=user_images,summary=session_data.get("summary"),num_images=num_images,base_cost=base_cost,duration=duration,height=height,width=width,aspect_ratio=aspect_ratio)

                    
                    if ai_response:
                        image_blocks=[]
                        images=ai_response.get("images", [])


                        images = await sync_to_async(download_and_store_webp)(image_urls=images)
                        images = [img for img in images]
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
                    print("error is occure ")
                    await self.send(text_data=json.dumps({"type": "error", "message": f"AI error: {str(e)}"},ensure_ascii=False))
        


        elif provider=='leonardo':
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
                    base_cost=getattr(model,"base_cost",500)
                    ai_response=await database_sync_to_async(leonardo_response)(
                        prompt=message_content,user_id=self.user.id,model_id=model_id,api_key=api_key,num_images=num_images,width=width,height=height,summary=session_data.get("summary"),BASE_COST=base_cost
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
                            await self.send(text_data=json.dumps({"type": "new_message", "message": saved_ai_message},ensure_ascii=False))
                except Exception as e:
                    await self.send(text_data=json.dumps({"type": "error", "message": f"AI error: {str(e)}"},ensure_ascii=False))



        elif provider=="wavespeedai":
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
                base_cost=getattr(model,"base_cost",500)
                model_type=getattr(model,"model_type")
                print(model_type)
                
                #for chat model

                if model_type=="chat":
                   await self.send(text_data=json.dumps({"type": "error", "message": f"wave spped model not provide chat"},ensure_ascii=False))
                
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
                     
                    ai_response=await database_sync_to_async(wavespeed_ai_call)(
                        model_id=model_id,
                        api_key=api_key,
                        payload=payload,
                        user_id=self.user.id,
                        base_cost=base_cost,
                        use_id= self.user.id
                    )
                    
                    if ai_response:
                        print("AI RESPONSE FROM WEAVESPEEDAI:",ai_response)
                        images=ai_response.get("images", [])
                        print(images,"video")
                        images = await sync_to_async(download_and_store_webp)(image_urls=images)
                        images = [img for img in images]
                        print(images)
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
                      await self.send(text_data=json.dumps({"type": "error", "message": f"AI error: {str(e)}"},ensure_ascii=False))
                
                #text to video generation
                elif model_type=="text_to_video":
                    try:
                        ai_response=await database_sync_to_async(text_to_video_generation)(
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
                         saved_ai_message = await self.save_message(
                            self.session_id,
                            self.user,
                            "ai",
                            content = "Video generated successfully.",
                            images=[ai_response]
                        )
                         if saved_ai_message:
                            await self.send(text_data=json.dumps({"type": "new_message", "message": {"text":"Video generated successfully.","video_url":ai_response}},ensure_ascii=False))
                            
                    except Exception as e:
                        await self.send(text_data=json.dumps({"type": "error", "message": f"AI error: {str(e)}"},ensure_ascii=False))
                        return
                elif model_type=="image_tool":
                    print("images",image[0])
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
                            saved_ai_message=await self.save_message(
                                self.session_id,
                                self.user,
                                "ai",
                                content="Image processed successfully",
                                images=[ai_response]
                            )
                            if saved_ai_message:
                                await self.send(text_data=json.dumps({"type": "new_message", "message": saved_ai_message},ensure_ascii=False))
                    except Exception as e:
                        await self.send(text_data=json.dumps({"type": "error", "message": f"AI error: {str(e)}"},ensure_ascii=False))
                        return
                elif model_type=="video_upscaler":
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
                                content="Image upscaled successfully",
                                images=[ai_response]
                            )
                            if saved_ai_message:
                                await self.send(text_data=json.dumps({"type": "new_message", "message": saved_ai_message},ensure_ascii=False))
                    except Exception as e:
                        await self.send(text_data=json.dumps({"type": "error", "message": f"AI error: {str(e)}"},ensure_ascii=False))
                        return
                

                elif model_type=="image_editor":

                    
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
                                content="Image edited successfully",
                                images=[ai_response]
                            )
                            if saved_ai_message:
                                await self.send(text_data=json.dumps({"type": "new_message", "message": saved_ai_message},ensure_ascii=False))

                       

                    
                    except Exception as e:
                        await self.send(text_data=json.dumps({"type": "error", "message": f"AI error: {str(e)}"},ensure_ascii=False))
                        return
                elif model_type=="image_to_3d":
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
                                content="3d image succesfully genereated",
                                images=[ai_response]
                            )
                        if saved_ai_message:
                                await self.send(text_data=json.dumps({"type": "new_message", "message": saved_ai_message},ensure_ascii=False))

                    except Exception as e:
                        await self.send(text_data=json.dumps({"type":"error","message":f"AI error: {str(e)}"},ensure_ascii=False))
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
                                content="Video Generated successfully",
                                images=[ai_response]
                        )
                           if saved_ai_message:
                                await self.send(text_data=json.dumps({"type": "new_message", "message": saved_ai_message},ensure_ascii=False))


                    except Exception as e:
                        await self.send(text_data=json.dumps({"type":"error","message":f"AI error: {str(e)}"},ensure_ascii=False))
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
                                content="Video Generated successfully",
                                images=[ai_response]
                        )
                           if saved_ai_message:
                                await self.send(text_data=json.dumps({"type": "new_message", "message": saved_ai_message},ensure_ascii=False))


                    except Exception as e:
                        await self.send(text_data=json.dumps({"type":"error","message":f"AI error: {str(e)}"},ensure_ascii=False))

                
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
            base_cost=getattr(model,"base_cost",1)

            ai_response=await database_sync_to_async(call_deepseek_for_chat)(
                user_id=self.user,
                model_id=model_id,
                api_key=api_key,
                base_cose=base_cost,
                message=message_content
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
                            await self.send(text_data=json.dumps({"type": "new_message", "message": saved_ai_message},ensure_ascii=False))
                

        

        elif provider=="falai":
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
                    base_cost=getattr(model,"base_cost",500)
                    ai_response = await database_sync_to_async(call_fal_ai)(
                        api_key, message_content,model_id,self.user.id,num_images,base_cost,seed,steps,cfg_scale,size
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
                            await self.send(text_data=json.dumps({"type": "new_message", "message": saved_ai_message},ensure_ascii=False))
                except Exception as e:
                    await self.send(text_data=json.dumps({"type": "error", "message": f"AI error: {str(e)}"},ensure_ascii=False))        
        else:
            await self.send(text_data=json.dumps({"type": "error", "message": f"Unsupported provider: {provider}"},ensure_ascii=False))
      
    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name ,self.channel_name)
