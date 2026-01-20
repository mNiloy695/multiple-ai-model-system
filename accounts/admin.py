from unfold.admin import ModelAdmin
from django.contrib import admin

from .models import CustomUser,OTP,CreditTransaction,CreditAccount,UserProfile
# Register your models here.

@admin.register(CustomUser)
class CustomUserAdmin(ModelAdmin):
    list_display = ('id', 'email', 'username', 'is_staff', 'is_active')
    search_fields = ('email', 'username')
    list_filter = ('is_staff', 'is_active')
    list_per_page=20
    ordering = ('id',)

@admin.register(OTP)
class OTPAdmin(ModelAdmin):
    list_display = ('id', 'user', 'code', 'type', 'created_at')
    search_fields = ('user__email', 'code', 'type')
    list_filter = ('type', 'created_at')
    ordering = ('-created_at',)
    list_per_page=20

@admin.register(CreditAccount)
class CreditAccountAdmin(ModelAdmin):
    list_display = ('id', 'user', 'credits')
    search_fields = ('user__email',)
    ordering = ('id',)
    list_per_page=20

@admin.register(CreditTransaction)
class CreditTransactionAdmin(ModelAdmin):
    list_display = ('id', 'credit_account', 'amount', 'transaction_type', 'created_at')
    search_fields = ('credit_account__user__email', 'transaction_type')
    list_filter = ('transaction_type', 'created_at')
    ordering = ('-created_at',)
    list_per_page=20

@admin.register(UserProfile)
class UserProfileAdmin(ModelAdmin):
    list_display = ('id', 'user', 'first_name', 'last_name', 'created_at')
    search_fields = ('user__email', 'first_name', 'last_name')
    ordering = ('id',)
    list_per_page=20


# @admin.register(UsageLog)
# class UsageLogAdmin(admin.ModelAdmin):
#     list_display = ('id', 'user', 'request_id', 'cost')
#     search_fields = ('user__email', 'request_id')
#     ordering = ('id',)