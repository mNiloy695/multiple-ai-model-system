from django.contrib import admin
from .models import AIModelInfo,ChatSession,ChatMessage

# Register your models here.

@admin.register(AIModelInfo)
class AdminAImodelInfor(admin.ModelAdmin):
    list_display=['id','provider','model_id','is_active']

@admin.register(ChatSession)
class AdminChatSession(admin.ModelAdmin):
    list_display=['id','summary','user']


