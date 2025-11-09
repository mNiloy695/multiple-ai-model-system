from django.urls import path,include
from .views import InvoiceView
from rest_framework.routers import DefaultRouter
router=DefaultRouter()
router.register('list',InvoiceView)

urlpatterns = [
    path('',include(router.urls)),
]
