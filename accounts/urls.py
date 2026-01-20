from .views import RegisterView, ActivateAccountView, LoginView,LogoutView,CreditTransactionHistoryView,GoogleLoginAPIView,ForgotPasswordView,ResetView,ProfileView,CreditAccountView
from django.urls import path,include
from rest_framework.routers import DefaultRouter
router=DefaultRouter()
router.register('profile',ProfileView,basename='profile')
urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('activate/', ActivateAccountView.as_view(), name='activate'),
    path('login/', LoginView.as_view(), name='login'),
    path('google/login/',GoogleLoginAPIView.as_view(),name='google-login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('transactions/', CreditTransactionHistoryView.as_view(), name='transaction-history'),
    path('forgot-password/',ForgotPasswordView.as_view(),name="forgot-password"),
    path('reset-password/',ResetView.as_view(),name='reset-password'),
    path('credit-account/',CreditAccountView.as_view(),name='credit-account'),
    path('',include(router.urls)),
    
]