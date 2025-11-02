from .views import RegisterView, ActivateAccountView, LoginView,LogoutView,CreditTransactionHistoryView
from django.urls import path
urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('activate/', ActivateAccountView.as_view(), name='activate'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('transactions/', CreditTransactionHistoryView.as_view(), name='transaction-history'),
    
]