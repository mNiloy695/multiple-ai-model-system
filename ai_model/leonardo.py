import requests
from accounts.models import CreditAccount, User
from .track_used_word_subscription import trackUsedWords
from .image_to_url_save import download_and_store_webp  # your existing function
import math

# Helper: Count Words (1 word = 5 non-space chars)
def count_words(text):
    if not text:
        return 0
    char_count = len(text.replace(" ", ""))
    return math.ceil(char_count / 5)

# Cache for model_id → allowed_resolutions
MODEL_INFO_CACHE = {}

def refresh_model_info(api_key):
    """
    Fetches Leonardo models and caches allowed resolutions for each model_id.
    """
    url = "https://cloud.leonardo.ai/api/rest/v1/models"
    headers = {"Authorization": f"Bearer {api_key}"}
    resp = requests.get(url, headers=headers, timeout=30)
    resp.raise_for_status()
    models = resp.json().get("models", [])
    for m in models:
        model_id = m["id"]
        allowed = m.get("allowed_resolutions") or [256, 512, 768, 1024]
        MODEL_INFO_CACHE[model_id] = allowed

def leonardo_response(
    prompt: str,
    user_id: int,
    model_id: str,
    num_images: int = 1,
    width: int = 512,
    height: int = 512,
    api_key: str = None,
    BASE_COST: int = 500,
    max_images_per_request: int = 1,
):
    try:
    
        # -------------------------
        user = User.objects.filter(id=user_id).first()
        if not user:
            return {"images": [], "error": "User not found.", "sender": "system"}

        credit_account = CreditAccount.objects.filter(user=user).first()
        if not credit_account:
            
            # return {"images": [], "error": "Credit account not found.", "sender": "system"}
            credit_account=CreditAccount.objects.create(user=user,credits=0)

        if not api_key:
            return {"images": [], "error": "API key missing.", "sender": "system"}

        
        if model_id not in MODEL_INFO_CACHE:
            refresh_model_info(api_key)

        allowed_sizes = MODEL_INFO_CACHE.get(model_id)
        if not allowed_sizes:
            return {"images": [], "error": f"Unknown model {model_id}", "sender": "system"}

        
        if width not in allowed_sizes or height not in allowed_sizes:
            width = max([s for s in allowed_sizes if s <= width], default=min(allowed_sizes))
            height = max([s for s in allowed_sizes if s <= height], default=min(allowed_sizes))

        num_images = min(num_images, max_images_per_request)

      
        # resolution_factor = (width * height) / (512 * 512)

        image_cost = int(BASE_COST)
        total_cost = image_cost * num_images

        if credit_account.credits < total_cost:
            return {"images": [], "error": "Not enough credits for requested image(s).", "sender": "system"}

        
        credit_account.credits -= total_cost
        if credit_account.credits < 0:
            credit_account.credits = 0
        credit_account.save()
        # Non-char models (image) don't track prompt words cost/usage
        user.total_token_used += total_cost # Track by cost instead
        user.save()

        payload = {
            "prompt": prompt,
            "num_images": num_images,
            "width": width,
            "height": height,
            "modelId": model_id
        }
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        response = requests.post("https://cloud.leonardo.ai/api/rest/v1/generations", json=payload, headers=headers, timeout=60)

        if response.status_code != 200:
            # Refund credits if API fails
            credit_account.credits += total_cost
            credit_account.save()
            return {"images": [], "error": f"Leonardo API error: {response.status_code} {response.text}", "sender": "system"}
        else:
            trackUsedWords(user.id, total_cost)

        data = response.json()
        temp_urls = []
        for img_block in data.get("sdGenerationJob", {}).get("generated_images", []):
            url = img_block.get("url")
            if url:
                temp_urls.append(url)

        
        permanent_urls = download_and_store_webp(temp_urls)

        return {"images": permanent_urls, "error": None, "sender": "ai"}

    except Exception as e:
        if 'credit_account' in locals():
            credit_account.credits += total_cost
            credit_account.save()
        error_str = str(e)
        if "api" in error_str.lower() or "key" in error_str.lower():
            return {"images": [], "error": "Authentication failed: Invalid API key.", "sender": "system"}
        return {"images": [], "error": "Unexpected error occurred. Please try again later.", "sender": "system"}
