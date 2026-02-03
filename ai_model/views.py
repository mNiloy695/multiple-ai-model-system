from django.shortcuts import render

# Create your views here.

from .serializers import AIModelSerializer,AIModelLimitedSerializer
from rest_framework import viewsets
from .models import AIModelInfo, ChatSession
from rest_framework import permissions, viewsets
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q

class AImodelView(viewsets.ModelViewSet):
    queryset = AIModelInfo.objects.all()
    serializer_class = AIModelSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['model_id', 'model_type', 'provider']
    # permission_classes = [permissions.IsAuthenticated]

    def get_permissions(self):
        if self.request.method in permissions.SAFE_METHODS:
            return [permissions.IsAuthenticated()]
        return [permissions.IsAdminUser()]

    def get_queryset(self):
        queryset = self.queryset

        
        if not (self.request.user and self.request.user.is_staff):
            queryset = queryset.filter(is_active=True).only(
                'id',
                'name',
                'model_id',
                'created_at',
                'description',
                'base_url',
                'provider',
                'model_type',
            )

        model_type = self.request.query_params.get('model_type')

        if model_type == 'text_to_video':
            queryset = queryset.filter(
                Q(model_type='text_to_video')
                | Q(model_type='text_or_image_to_video')
            )

        elif model_type == 'image_to_video':
            queryset = queryset.filter(
                Q(model_type='image_to_video')
                | Q(model_type='text_or_image_to_video')
            )

        return queryset

    def get_serializer_class(self):
        if self.request.user and self.request.user.is_staff:
            return AIModelSerializer
        return AIModelLimitedSerializer

from .serializers import ChatSessionSerializer

from django.utils.translation import gettext as _

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
    
    def validate_session_type(self,attrs):
        session_type=attrs.get('session_type',None)
        if not session_type:
            raise ValueError({"error": _("Session type is required")})

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        # text = serializer.validated_data.get('text', True)
        # is_text = text if isinstance(text, bool) else bool(text)
        session_type=serializer.validated_data.get('session_type',None)
        print(session_type)
        # model = AIModelInfo.objects.filter(
        #     session_type=session_type,
        #     is_active=True
        # ).order_by('-created_at').first()

        model=serializer.validated_data.get('model',None)
        
       

        if not model:
            return Response({"error": _("No {} active AI models available.").format(session_type)}, status=400)
        # Check for previous empty session
        previous_session = ChatSession.objects.filter(user=request.user).order_by('-created_at').first()
        if previous_session and not previous_session.messages.exists():
            # Reuse previous session
            previous_session.model = model 
            previous_session.session_type=session_type
            previous_session.save()
            data = self.get_serializer(previous_session).data
            return Response(data, status=200)


       
        
        serializer.save(model=model, user=request.user)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=201, headers=headers)
 




