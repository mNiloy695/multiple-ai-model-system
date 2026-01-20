from django.contrib import admin
from unfold.admin import ModelAdmin
from .models import InvoiceModel
# Register your models here.

@admin.register(InvoiceModel)
class InvoiceModelAdmin(ModelAdmin):
    list_display=['invoice_id','plan','user__email','amount']
    list_per_page=20
