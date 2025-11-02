from django.urls import path,include
from . import views
from rest_framework.routers import DefaultRouter

router=DefaultRouter()
router.register('list',views.AImodelView,basename='ai-model')
router.register('chat/session/list/',views.ChatSessionView,basename='chat-session-view')
urlpatterns = [
    path('',include(router.urls)),

]
