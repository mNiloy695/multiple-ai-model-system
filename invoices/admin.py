from django.contrib import admin
from .models import InvoiceModel
# Register your models here.

@admin.register(InvoiceModel)
class InvoiceModelAdmin(admin.ModelAdmin):
    list_display=['invoice_id','plan','user__email','amount']
