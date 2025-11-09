from django.shortcuts import render
from .serializers import InvoiceSerializer
from .models import InvoiceModel
from rest_framework import permissions
# Create your views here.

from rest_framework import viewsets

class InvoiceView(viewsets.ModelViewSet):
    queryset=InvoiceModel.objects.select_related('user','plan')
    serializer_class=InvoiceSerializer


    def get_permissions(self):
        if self.request.method in permissions.SAFE_METHODS:
            return [permissions.IsAuthenticated()]
        return [permissions.IsAdminUser()]
    
    def get_queryset(self):
        user=self.request.user

        if not user.is_staff:
            return self.queryset.filter(user=user)
        return self.queryset.all()