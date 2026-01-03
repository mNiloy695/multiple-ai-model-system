from openai import OpenAI
from django.contrib.auth import get_user_model
from accounts.models import CreditAccount
from .openai_func import _error

User = get_user_model()

MODEL_LIMIT = 4096
TOKEN_PER_WORD = 1.3

def call_deepseek_for_chat(model_id, api_key, user_id, base_cost, message, temperature=0.7):
    try:
        user = User.objects.get(id=user_id)
        account = CreditAccount.objects.get(user=user)
    except User.DoesNotExist:
        return _error("User not found")
    except CreditAccount.DoesNotExist:
        return _error("Account not found")

    
    input_words = len(message.split())
    input_tokens = int(input_words * TOKEN_PER_WORD)

    if account.credits < input_tokens:
        return _error("Insufficient Credits")

    
    available_tokens = min(
        int(account.credits - input_tokens),
        MODEL_LIMIT - input_tokens
    )

    if available_tokens <= 0:
        return _error("Not enough credits for response")

    try:
        client = OpenAI(
            api_key=api_key,
            base_url="https://api.deepseek.com"
        )

        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": "You are a helpful assistant"},
                {"role": "user", "content": message},
            ],
            max_tokens=available_tokens,
            temperature=temperature,
        )

        reply_text = response.choices[0].message.content

        
        output_tokens = int(len(reply_text.split()) * TOKEN_PER_WORD)

        total_tokens_used = input_tokens + output_tokens

        
        account.credits -= total_tokens_used
        account.user.total_token_used += total_tokens_used
        account.user.save()
        account.save()

        return {"text": reply_text}

    except Exception as e:
        return {"error": "An error occurred"}
