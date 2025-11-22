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
    


    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        text = serializer.validated_data.get('text', True)
        is_text = text if isinstance(text, bool) else bool(text)
        model = AIModelInfo.objects.filter(
            images_generating_models=not is_text,
            is_active=True
        ).order_by('-created_at').first()
        
        if not model:
            model = AIModelInfo.objects.filter(is_active=True).order_by('-created_at').first()
        if not model:
            return Response({"error": "No active AI models available."}, status=400)
        # Check for previous empty session
        previous_session = ChatSession.objects.filter(user=request.user).order_by('-created_at').first()
        if previous_session and not previous_session.messages.exists():
            # Reuse previous session
            previous_session.model = model  # optional update
            previous_session.save()
            data = self.get_serializer(previous_session).data
            return Response(data, status=200)

        # Otherwise, create a new session
       
        
        serializer.save(model=model, user=request.user)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=201, headers=headers)
    # def perform_create(self, serializer):
    #     # model_id = serializer.validated_data.get('model_id', 'gpt-3.5-turbo')
    #     text= serializer.validated_data.get('text', True)
    #     model_id=AIModelInfo.objects.filter(images_generating_models=not text,is_active=True).order_by('created_at').first()
    #     model=AIModelInfo.objects.filter(model_id=model_id).first()
    #     serializer.save(model=model,user=self.request.user)

