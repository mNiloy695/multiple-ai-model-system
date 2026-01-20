from django.contrib import admin
from unfold.admin import ModelAdmin
from .models import RewardsHistory      
# Register your models here.

@admin.register(RewardsHistory)
class ARewardsHistoryAdmin(ModelAdmin):
    list_display = ('id', 'user__email', 'reward', 'created_at')
    search_fields = ('user__email', 'reward')
    list_filter = ('reward', 'created_at')
    ordering = ('-created_at',)
    list_per_page = 20
