
from django.contrib.auth import get_user_model
from google import genai
from accounts.models import CreditAccount
from django.contrib.auth import get_user_model
import requests, base64

User = get_user_model()

def gemini_response(message, model_id, api_key, user_id, images_data_list=None,summary=None):
 
    try:
        client = genai.Client(api_key=api_key)

     
        user = User.objects.filter(id=user_id).first()
        if not user:
            return {"text": "", "images": [], "sender": "system", "error": "User not found."}

        credit_account = CreditAccount.objects.filter(user=user).first()
        if not credit_account:
            return {"text": "", "images": [], "sender": "system", "error": "Credit account not found."}

        
        prompt_words = len(message.split())
        if credit_account.credits < prompt_words:
            return {"text": "", "images": [], "sender": "system", "error": "Insufficient credits for prompt."}
        
      

        supports_image = not (
            "lite" in model_id.lower() or
            "tts" in model_id.lower() or
            "audio" in model_id.lower() or
            "embedding" in model_id.lower()
        )

        if images_data_list and not supports_image:
            return {
                "text": f" The selected model '{model_id}' does not support image input.",
                "images": [],
                "sender": "system",
                "error": None
            }
        contents=[]
        if summary:
            contents.append(
                {
                    "role":"system",
                    "parts":[{"text":f"Conversation summary so far: {summary}"}]
                }
            )
        contents.append({"role": "user", "parts": [{"text": message}]})

        # contents = [{"role": "user", "parts": [{"text": message}]}]

        if images_data_list and supports_image:
            user_index = 1 if summary else 0
            for img in images_data_list:
                try:
                   
                    if isinstance(img, str) and img.startswith("http"):
                        resp = requests.get(img)
                        resp.raise_for_status()
                        img_data = base64.b64encode(resp.content).decode("utf-8")
                        contents[user_index]["parts"].append({
                            "inline_data": {
                                "mime_type": "image/png",
                                "data": img_data
                            }
                        })

                    # If it's already base64
                    elif isinstance(img, str):
                        contents[user_index]["parts"].append({
                            "inline_data": {
                                "mime_type": "image/png",
                                "data": img
                            }
                        })
                except Exception as e:
                    return {
                        "text": f"Failed to fetch or convert image: {img}. Error: {str(e)}",
                        "images": [],
                        "sender": "system",
                        "error": None
                    }
        
      
        
        response = client.models.generate_content(model=model_id, contents=contents)

    
        text = getattr(response, "text", "")
        if not text and hasattr(response, "candidates") and response.candidates:
            candidate_parts = response.candidates[0].content.parts
            text_parts = [getattr(p, "text", "") for p in candidate_parts if getattr(p, "text", None)]
            text = " ".join(text_parts)

        response_words = len(text.split())
        if response_words + prompt_words > credit_account.credits:
           allowed_words = credit_account.credits - prompt_words
           words = text.split()
           text = " ".join(words[:allowed_words])
           response_words = allowed_words

        credit_account.credits -= (prompt_words + response_words)
        credit_account.save()

       

        images = []
        if supports_image and hasattr(response, "candidates") and response.candidates:
            
            for part in response.candidates[0].content.parts:
                if hasattr(part, "inline_data") and hasattr(part.inline_data, "data"):
                    images.append(f"data:image/png;base64,{part.inline_data.data}")

        return {"text": text, "images": images, "sender": "ai", "error": None}

    except Exception as e:
        return {"text": "", "images": [], "sender": "system", "error": f"Gemini request failed: {str(e)}"}