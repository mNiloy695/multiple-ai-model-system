
from django.contrib.auth import get_user_model

from google import genai
from accounts.models import CreditAccount
from django.contrib.auth import get_user_model

import requests, base64
from openai import OpenAI


User = get_user_model()


def gpt_response(message, model_id, api_key, user_id, images_data_list=None, max_response_tokens=1000):
   
    try:
        client = OpenAI(api_key=api_key)

        
        user = User.objects.filter(id=user_id).first()
        if not user:
            return {"text": "", "images": [], "sender": "system", "error": "User not found."}

        credit_account = CreditAccount.objects.filter(user=user).first()
        if not credit_account:
            return {"text": "", "images": [], "sender": "system", "error": "Credit account not found."}

        prompt_words = len(message.split())
        if credit_account.credits < prompt_words:
            return {"text": "", "images": [], "sender": "system", "error": "Insufficient credits for prompt."}

        
        credit_account.credits -= prompt_words
        credit_account.save()

        
        chat_models = ["gpt-3.5-turbo", "gpt-4", "gpt-4o", "gpt-4-vision", "gpt-5"]
        image_models = ["dall-e", "gpt-image", "gpt-4-vision"] 
        is_chat_model = any(k in model_id.lower() for k in chat_models)
        supports_image = any(k in model_id.lower() for k in image_models)

        if images_data_list and not supports_image:
            return {
                "text": f"The selected model '{model_id}' does not support image input.",
                "images": [],
                "sender": "system",
                "error": None
            }

        
        messages = [{"role": "user", "content": message}] if is_chat_model else None
        prompt = message if not is_chat_model else None

        
        image_blocks = []
        if images_data_list and supports_image:
            for img in images_data_list:
                try:
                    if img.startswith("http"):
                        resp = requests.get(img)
                        resp.raise_for_status()
                        img_data = base64.b64encode(resp.content).decode("utf-8")
                    else:
                        img_data = img  

                    image_blocks.append(f"data:image/png;base64,{img_data}")
                except Exception as e:
                    
                    continue

       
        text = ""
        images = []

        try:
            if is_chat_model:
                chat_content = [{"role": "user", "content": message}]
                response = client.chat.completions.create(
                    model=model_id,
                    messages=chat_content,
                    max_tokens=max_response_tokens
                )
                if response.choices:
                    text = response.choices[0].message.content.strip()
            else:
                response = client.completions.create(
                    model=model_id,
                    prompt=prompt,
                    max_tokens=max_response_tokens
                )
                if response.choices:
                    text = response.choices[0].text.strip()

        except Exception as e:
            
            credit_account.credits += prompt_words
            credit_account.save()
            return {"text": "", "images": [], "sender": "system", "error": f"GPT request failed: {str(e)}"}

        
        response_words = len(text.split())
        if response_words > credit_account.credits:
            allowed = credit_account.credits
            text = " ".join(text.split()[:allowed])
            response_words = allowed

        credit_account.credits -= response_words
        credit_account.save()

       
        if supports_image:
            images = image_blocks  

        return {"text": text, "images": images, "sender": "ai", "error": None}

    except Exception as e:
        return {"text": "", "images": [], "sender": "system", "error": f"Unexpected error: {str(e)}"}