from django.contrib import admin
from .models import CustomUser,OTP
# Register your models here.

@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ('id', 'email', 'username', 'is_staff', 'is_active')
    search_fields = ('email', 'username')
    list_filter = ('is_staff', 'is_active')
    ordering = ('id',)

@admin.register(OTP)
class OTPAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'code', 'type', 'created_at')
    search_fields = ('user__email', 'code', 'type')
    list_filter = ('type', 'created_at')
    ordering = ('-created_at',)
