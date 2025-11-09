from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings
import stripe
from .models import PlanModel

from rest_framework import permissions
from rest_framework import viewsets
from .serializers import PlanSerializer

from django.contrib.auth import get_user_model
User=get_user_model()



#Plan model views

class PlanView(viewsets.ModelViewSet):
    permission_classes=[permissions.IsAdminUser]
    queryset=PlanModel.objects.all().order_by('-created_at')
    serializer_class=PlanSerializer



stripe.api_key = settings.STRIPE_SECRET_KEY
print("stripe apie kye",stripe.api_key)

class CreateCheckoutSessionView(APIView):
    permission_classes=[permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        try:
            data = request.data
            plan_id=data.get('plan')
            user=request.user

            try: 
                plan=PlanModel.objects.get(id=plan_id)
            except Exception as e:
                 return Response({"error:":"Plan Model not found"})


            if not plan.stripe_product_price_id:
                return Response({"error": "Price ID is required the plan not have price id"}, status=status.HTTP_400_BAD_REQUEST)
            price_id=plan.stripe_product_price_id
            
            session = stripe.checkout.Session.create(
                payment_method_types=["card",],
                
                line_items=[{
                    "price": price_id,
                    "quantity": 1,
                }],
                mode="payment",
                metadata={
        "user_id": str(user.id),
        "words": str(plan.words_or_credits),
        "price_id":str(price_id)
    },
                success_url="http://127.0.0.1:8081/api/v1/success?session_id={CHECKOUT_SESSION_ID}",
                cancel_url="http://127.0.0.1:8081/api/v1/cancel",
            )

            return Response({"checkout_url": session.url})

        except Exception as e:
            return Response({"error ms": str(e)}, status=status.HTTP_400_BAD_REQUEST)



from .models import Revenue
from django.db.models import Sum
class TotalRevenueView(APIView):
    permission_classes=[permissions.IsAdminUser]
    
    def get(self, request, *args, **kwargs):
        total_revenue=Revenue.objects.aggregate(total=Sum('amount'))['total'] or 0
        return Response({
            'revenue':total_revenue
        })

        



#google payment 


from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from invoices.models import InvoiceModel as Invoice

# class VerifyGooglePurchaseView(APIView):
#     def post(self, request):
#         token = request.data.get("purchase_token")
#         product_id = request.data.get("product_id")
#         package_name = settings.GOOGLE_PACKAGE_NAME

#         url = f"https://androidpublisher.googleapis.com/androidpublisher/v3/applications/{package_name}/purchases/products/{product_id}/tokens/{token}?access_token={settings.GOOGLE_API_ACCESS_TOKEN}"
#         r = requests.get(url)
#         data = r.json()

#         if data.get("purchaseState") == 0:
#             # purchase is valid
#             return Response({"status": "success"})
#         return Response({"status": "invalid"})


# views.py


from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from google.oauth2 import service_account
from google.auth.transport.requests import Request
from django.conf import settings
from django.shortcuts import get_object_or_404
import requests
from invoices.models import InvoiceModel as Invoice


class VerifyGooglePurchaseView(APIView):
    permission_classes=[permissions.IsAuthenticated]
    def post(self, request):
        plan_id = request.data.get("plan")
        purchase_token = request.data.get("purchase_token")

        # 1️⃣ Fetch plan info
        plan = get_object_or_404(PlanModel, id=plan_id)
        product_id = plan.stripe_product_price_id

        # 2️⃣ Create credentials from service account
        credentials = service_account.Credentials.from_service_account_file(
            settings.GOOGLE_SERVICE_ACCOUNT_FILE,
            scopes=["https://www.googleapis.com/auth/androidpublisher"]
        )
        credentials.refresh(Request())
        access_token = credentials.token

        # 3️⃣ Verify purchase with Google Play API
        url = (
            f"https://androidpublisher.googleapis.com/androidpublisher/v3/applications/"
            f"{settings.GOOGLE_PACKAGE_NAME}/purchases/products/{product_id}/tokens/{purchase_token}"
        )
        headers = {"Authorization": f"Bearer {access_token}"}
        response = requests.get(url, headers=headers)
        data = response.json()

        # 4️⃣ Check Google’s response
        if data.get("purchaseState") == 0:  # 0 = purchased
            user = request.user
            user.credits += plan.words_or_credits
            user.save()
            Revenue.objects.create(
                    user=user,
                    plan=plan,
                    amount=plan.amount,
                    payment_id=data.get('orderId'),
                    
                )

            Invoice.objects.create(
                invoice_id=f"INV-{data.get('orderId')}",
                user=user,
                plan=plan,
                amount=plan.amount,
                payment_status="paid",
            )

            return Response({
                "status": "success",
                "message": f"{plan.name} plan activated",
                "credits_added": plan.words_or_credits
            })

        return Response({
            "status": "failed",
            "message": "Invalid or unverified purchase",
            "google_response": data
        }, status=status.HTTP_400_BAD_REQUEST)

