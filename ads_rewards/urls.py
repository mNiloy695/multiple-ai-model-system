from django.urls import path,include
from rest_framework.routers import DefaultRouter
from .views import RewardsHistoryView
router=DefaultRouter()
router.register('rewards',RewardsHistoryView)
urlpatterns=[
    path('',include(router.urls))
]