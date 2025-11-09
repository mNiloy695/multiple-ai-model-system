from django.urls import path,include
from .views import CreateCheckoutSessionView,PlanView,TotalRevenueView,VerifyGooglePurchaseView
from rest_framework.routers import DefaultRouter
from .webhook import stripe_webhook
router=DefaultRouter()
router.register('list',PlanView,basename='plan')
urlpatterns = [
    path('checkout/',CreateCheckoutSessionView.as_view()),
    path('webhook/',stripe_webhook),
    path('',include(router.urls)),
    path('revenue/',TotalRevenueView.as_view(),name='revenue'),
    path('checkout/google-pay/',VerifyGooglePurchaseView.as_view()),

]
