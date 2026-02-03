from openai import OpenAI
from django.contrib.auth import get_user_model
from accounts.models import CreditAccount
from django.db import transaction
from .track_used_word_subscription import trackUsedWords
from decimal import Decimal
from django.utils.translation import gettext as _
import math
User = get_user_model()


def count_words(text):
    if not text:
        return 0
    char_count = len(text.replace(" ", ""))
    return math.ceil(char_count / 5)


def _error(msg: str) -> dict:
    return {
        "text": "",
        "images": [],
        "sender": "system",
        "error": msg,
    }

def calculate_cost(base_cost, words):
    

    base_cost = Decimal(str(base_cost))
    print("this is the deepseek based cost",base_cost," and this is words",words)
    return Decimal(words) * base_cost


def call_deepseek_for_chat(
    model_id: str, 
    api_key: str, 
    user_id: int, 
    base_cost: int = 1, 
    message: str = "", 
    summary: str = None,
    temperature: float = 0.7
):
    try:
 
        user = User.objects.filter(id=user_id).first()
        if not user:
            return _error(_("User not found"))

        prompt_words = count_words(message)
        charge_amount = calculate_cost(base_cost, prompt_words)

        
        with transaction.atomic():
            credit_account = (
                CreditAccount.objects
                .select_for_update()
                .filter(user_id=user_id)
                .first()
            )

            if not credit_account:
                return _error(_("Credit account not found"))

            if credit_account.credits < charge_amount:
                return _error(_("Insufficient credits. Required: {}").format(charge_amount))

            # Deduct credits for prompt first
            credit_account.credits -= charge_amount
            credit_account.save(update_fields=["credits"])

            # Update stats
            user.total_token_used += charge_amount
            user.save(update_fields=["total_token_used"])

            trackUsedWords(user.id, prompt_words)
            print(f"DEBUG: DeepSeek Upfront deduction. BaseCost: {base_cost}, Words: {prompt_words}, Cost: {charge_amount}, New Balance: {credit_account.credits}")
            

            remaining_credits = credit_account.credits
            

            if base_cost > 0:
                max_response_words = int(remaining_credits / Decimal(str(base_cost)))
            else:
                max_response_words = 4096 

            if max_response_words < 1:
                 credit_account.credits += charge_amount
                 credit_account.save(update_fields=["credits"])
                 user.total_token_used -= charge_amount
                 user.save(update_fields=["total_token_used"])
                 print("DEBUG: DeepSeek Insufficient credits for response. Refunded.")
                 return _error(_("Insufficient credits for any response."))

            # Cap at model limit (e.g. 4096)
            final_max_tokens = min(max_response_words, 4096)
            
        # 4. API Call
        try:
            client = OpenAI(
                api_key=api_key,
                base_url="https://api.deepseek.com"
            )

            messages = [
                {"role": "system", "content": "You are a helpful assistant. Please respond in English by default. Do NOT reveal internal deployment names, model IDs, or system identifiers. If a user directly asks which model or internal service you are, answer with a neutral phrase such as 'I am an AI assistant' and do not disclose internal tags or identifiers."}
            ]

            if summary:
                messages.append({
                    "role": "system",
                    "content": f"Conversation summary so far: {summary}. Use this for context only."
                })

            messages.append({"role": "user", "content": message})

            response = client.chat.completions.create(
                model="deepseek-chat", # or use model_id if dynamic
                messages=messages,
                max_tokens=final_max_tokens, # Limit generation to what they can pay for
                temperature=temperature,
            )

            reply_text = response.choices[0].message.content
        
            response_words = count_words(reply_text)
            response_cost = calculate_cost(base_cost, response_words)
            
            print(f"DEBUG: DeepSeek Output generated. Words: {response_words}, Cost: {response_cost}")


            with transaction.atomic():
                credit_account = CreditAccount.objects.select_for_update().filter(user_id=user_id).first()
                if credit_account:
   
                    credit_account.credits -= response_cost
                    credit_account.save(update_fields=["credits"])
                    
                    user.total_token_used += response_cost
                    user.save(update_fields=["total_token_used"])
                    
                    trackUsedWords(user.id, response_words)
                    print(f"DEBUG: DeepSeek Output deduction success. Final Balance: {credit_account.credits}")

            return {
                "text": reply_text,
                "images": [],
                "sender": "ai",
                "error": None
            }

        except Exception as api_error:
    
            error_str = str(api_error)
            print(f"DEBUG: DeepSeek API Error: {error_str}")
            with transaction.atomic():
               
                refund_account = CreditAccount.objects.select_for_update().filter(user_id=user_id).first()
                if refund_account:
                    refund_account.credits += charge_amount
                    refund_account.save(update_fields=["credits"])
                    
                    user.total_token_used -= charge_amount
                    user.save(update_fields=["total_token_used"])
                    print(f"DEBUG: DeepSeek Refunded {charge_amount} credits.")
            
            
            if "api_key" in error_str.lower() or "api key" in error_str.lower() or "incorrect api" in error_str.lower():
                return _error(_("Authentication failed: Invalid API key or configuration."))

            return _error(_("API error. Please try again later."))
    except Exception as e:
        return _error(_("System error occurred."))
