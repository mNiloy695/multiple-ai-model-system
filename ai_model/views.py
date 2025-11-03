from django.shortcuts import render

# Create your views here.

from .serializers import AIModelSerializer,AIModelLimitedSerializer
from rest_framework import viewsets
from .models import AIModelInfo,ChatSession
from rest_framework import permissions
from rest_framework.response import Response
class AImodelView(viewsets.ModelViewSet):
    queryset=AIModelInfo.objects.all()
    serializer=AIModelSerializer
    # permission_classes=[permissions.IsAdminUser]

    def get_permissions(self):
        if self.request.method in permissions.SAFE_METHODS:
            return [permissions.AllowAny()]
        return [permissions.IsAdminUser()]
    
    def get_queryset(self):
        
        if self.request.user and self.request.user.is_staff:
            return self.queryset.all()
        
        return self.queryset.filter(is_active=True).only('id','name','model_id','created_at','description','base_url')
    
    def get_serializer_class(self):
        if self.request.user and self.request.user.is_staff:
            return AIModelSerializer
        return AIModelLimitedSerializer

from .serializers import ChatSessionSerializer



# session management 

class CustomPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.user.is_authenticated:
            return True
        return False
    def has_object_permission(self, request, view, obj):
        return request.user.is_staff or obj.user==request.user
class ChatSessionView(viewsets.ModelViewSet):
    queryset=ChatSession.objects.all().prefetch_related('messages')
    serializer_class=ChatSessionSerializer
    permission_classes=[CustomPermission]

    def get_queryset(self):
        user=self.request.user

        if not user.is_staff:
            return self.queryset.filter(user=user).order_by('-created_at')
        
        return self.queryset.all().order_by('-created_at')
    def perform_create(self, serializer):
        model=AIModelInfo.objects.filter(model_id="gemini-2.5-flash").first()
        serializer.save(model=model,user=self.request.user)

