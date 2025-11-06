import requests, base64
from accounts.models import CreditAccount, User

def get_model_multiplier(model_id: str) -> float:
    model_id_lower = model_id.lower()
    if "anime" in model_id_lower:
        return 1.2
    elif "fantasy" in model_id_lower:
        return 1.5
    elif "digital" in model_id_lower or "art" in model_id_lower:
        return 1.3
    else:
        return 1.0

def leonardo_response(
    prompt,
    user_id,
    model_id,
    num_images=1,
    width=512,
    height=512,
    api_key=None,
    BASE_COST=2,
    max_images_per_request=4
):
    try:
        user = User.objects.filter(id=user_id).first()
        if not user:
            return {"images": [], "error": "User not found.", "sender": "system"}

        credit_account = CreditAccount.objects.filter(user=user).first()
        if not credit_account:
            return {"images": [], "error": "Credit account not found.", "sender": "system"}

        multiplier = get_model_multiplier(model_id)

       
        prompt_words = len(prompt.split())
        if credit_account.credits < prompt_words:
            return {"images": [], "error": "Insufficient credits for prompt.", "sender": "system"}
        credit_account.credits -= prompt_words
        credit_account.save()

     
        num_images = min(num_images, max_images_per_request)

        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "prompt": prompt,
            "num_images": num_images,
            "width": width,
            "height": height,
            "modelId": model_id
        }
        url = "https://cloud.leonardo.ai/api/rest/v1/generations"
        response = requests.post(url, json=payload, headers=headers)
        data = response.json()
        if response.status_code != 200:
               return {"images": [], "error": f"Leonardo API error: {response.status_code} {response.text}", "sender": "system"}

        
        images = []
        total_image_cost = 0
        for img_block in data.get("sdGenerationJob", {}).get("generated_images", []):
            total_image_cost += img_block.get("apiCreditCost", 0) or int(BASE_COST * (width*height)/(512*512) * multiplier)
            url = img_block.get("url")
            if url:
                img_resp = requests.get(url)
                img_data = base64.b64encode(img_resp.content).decode("utf-8")
                images.append(f"data:image/png;base64,{img_data}")

        # print("total cost",total_image_cost)
        if credit_account.credits < total_image_cost:
            
            max_affordable = credit_account.credits // int(BASE_COST * (width*height)/(512*512) * multiplier)
            images = images[:max_affordable]
            total_image_cost = max_affordable * int(BASE_COST * (width*height)/(512*512) * multiplier)
           

        credit_account.credits -= total_image_cost
        credit_account.save()
        # print(credit_account.credits)

        if not images:
            return {"images": [], "error": "Not enough credits for any image.", "sender": "system"}

        return {"images": images, "error": None, "sender": "ai"}

    except Exception as e:
        if 'credit_account' in locals():
            credit_account.credits += prompt_words
            credit_account.save()
        return {"images": [], "error": f"Unexpected error: {str(e)}", "sender": "system"}
