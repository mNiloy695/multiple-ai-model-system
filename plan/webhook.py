# payments/views.py
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import stripe
from AIModelBackend import settings
from accounts.models import CreditAccount,CreditTransaction
from django.db.models import F
import json
from .models import Revenue,PlanModel,SubscriptionModel
from django.contrib.auth import get_user_model
from invoices.models import InvoiceModel
from datetime import datetime, timezone, timedelta

# Get current UTC time
now_utc = datetime.now(timezone.utc)
print("Current UTC time:", now_utc)

# Create a timezone offset (e.g., UTC+6)
bd_timezone = timezone(timedelta(hours=6))
now_bd = datetime.now(bd_timezone)
print("Bangladesh time:", now_bd)

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
                if plan.subscription_duration !="one-time":
                    if plan.subscription_duration=="weekly":
                        expire_date=datetime.now(timezone.utc)+timedelta(days=7)
                    elif plan.subscription_duration=="monthly":
                        expire_date=datetime.now(timezone.utc)+timedelta(days=30)
                    elif plan.subscription_duration=="yearly":
                        expire_date=datetime.now(timezone.utc)+timedelta(days=365)

                    # subscription_id=metadata.get('subscription_id')
                    subs,created=SubscriptionModel.objects.get_or_create(
                    user=user,
                    plan=plan,
                    defaults={
                    "price":plan.amount,
                    "credits_words":plan.words_or_credits+account.credits,
                    "used_words":0,
                    "duration_type":plan.subscription_duration,
                    "start_date":datetime.now(timezone.utc),
                    "expire_date":expire_date,
                    
                    }
                    )
                   
                    if not created:
                        subs.price=plan.amount
                        subs.credits_words=plan.words_or_credits+account.credits
                        subs.used_words=0
                        subs.duration_type=plan.subscription_duration
                        subs.start_date=datetime.now(timezone.utc)
                        subs.expire_date=expire_date
                        
                        subs.save()
                    user.subscribed=True
                    user.save()
                
                
                
                payment_id=session.get('payment_intent')
                InvoiceModel.objects.create(
                    invoice_id=f"INV-{payment_id}",
                    user=user,
                    plan=plan,
                    amount=plan.amount,
                    payment_status="paid",

                )

            print("invoice")
            


            if not updated:
                return JsonResponse({'error': 'Credit Account Not Found'}, status=404)

   

        return JsonResponse({'status': 'success'})

    except ValueError as e:
      
        return JsonResponse({'error': 'Invalid payload'}, status=400)
    except stripe.error.SignatureVerificationError:
        
        return JsonResponse({'error': 'Invalid signature'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
