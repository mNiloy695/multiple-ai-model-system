from django.contrib import admin
from unfold.admin import ModelAdmin
from .models import AIModelInfo,ChatSession,ChatMessage

# Register your models here.

@admin.register(AIModelInfo)
class AdminAImodelInfor(ModelAdmin):
    list_display=['id','provider','model_id','is_active']
    search_fields = ('model_id', 'provider')
    list_filter = ('provider', 'model_id')
    list_per_page = 20

@admin.register(ChatSession)
class AdminChatSession(ModelAdmin):
    list_display=['id','summary','user']
    list_per_page = 20


admin.site.register(ChatMessage)


