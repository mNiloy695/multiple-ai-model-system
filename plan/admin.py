from django.contrib import admin
from .models import Revenue

# Register your models here.
@admin.register(Revenue)
class AdminRevenue(admin.ModelAdmin):
    list_display=['id','amount','user__email','payment_id','plan']

