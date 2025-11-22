from rest_framework import serializers
from .models import InvoiceModel




class InvoiceSerializer(serializers.ModelSerializer):
    plan_name = serializers.CharField(source='plan.name', read_only=True)
    class Meta:
        model=InvoiceModel
        fields=['invoice_id','date','amount','plan_name','plan']
