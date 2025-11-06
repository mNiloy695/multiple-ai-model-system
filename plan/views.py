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
                payment_method_types=["card"],
                line_items=[{
                    "price": price_id,
                    "quantity": 1,
                }],
                mode="payment",
                metadata={
        "user_id": str(user.id),
        "words": str(plan.words_or_credits)
    },
                success_url="http://127.0.0.1:8081/api/v1/success?session_id={CHECKOUT_SESSION_ID}",
                cancel_url="http://127.0.0.1:8081/api/v1/cancel",
            )

            return Response({"checkout_url": session.url})

        except Exception as e:
            return Response({"error ms": str(e)}, status=status.HTTP_400_BAD_REQUEST)
