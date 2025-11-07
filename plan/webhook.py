# payments/views.py
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import stripe
from AIModelBackend import settings
from accounts.models import CreditAccount,CreditTransaction
from django.db.models import F
import json
from .models import Revenue,PlanModel
from django.contrib.auth import get_user_model
User=get_user_model()
stripe.api_key = settings.STRIPE_SECRET_KEY
webhook_secret = settings.WEBHOOK_SECRET  

@csrf_exempt
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META.get("HTTP_STRIPE_SIGNATURE")

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, webhook_secret
        )

        
        if event['type'] == 'checkout.session.completed':
            session = event['data']['object']
            metadata = session.get('metadata', {})
            user_id = metadata.get('user_id')
            words = metadata.get('words', 0)
            price_id=metadata.get("price_id",None)

            try:
                
                words = int(words)
            except (ValueError, TypeError):
                return JsonResponse({'error': 'Invalid words value'}, status=400)
            
            account = CreditAccount.objects.filter(user_id=user_id).first()
            if not account:
              return JsonResponse({'error': 'Credit Account Not Found'}, status=404)

        
            updated = CreditAccount.objects.filter(user_id=user_id).update(
                credits=F('credits') + words
            )
            if account:
                CreditTransaction.objects.create(
                    credit_account=account,
                    amount=words,
                    transaction_type='add',
                    message=f'{words} credits added successfully in you account'

                )
            
            plan=PlanModel.objects.filter(stripe_product_price_id=price_id).first()
            user=User.objects.get(id=user_id)

            if plan and user:
                
                Revenue.objects.create(
                    user=user,
                    plan=plan,
                    amount=plan.amount,
                    payment_id=session.get('payment_intent')
                    
                )
            


            if not updated:
                return JsonResponse({'error': 'Credit Account Not Found'}, status=404)

        return JsonResponse({'status': 'success'})

    except ValueError as e:
      
        return JsonResponse({'error': 'Invalid payload'}, status=400)
    except stripe.error.SignatureVerificationError:
        
        return JsonResponse({'error': 'Invalid signature'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
