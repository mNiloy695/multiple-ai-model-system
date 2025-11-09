from rest_framework import serializers
from .models import InvoiceModel




class InvoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model=InvoiceModel
        fields=['invoice_id','date','amount','plan__name','plan']
