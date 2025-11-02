from rest_framework import serializers
from .models import AIModelInfo,ChatMessage,ChatSession

class AIModelSerializer(serializers.ModelSerializer):
    class Meta:
        model=AIModelInfo
        fields='__all__'
        read_only_fields=['created_at','updated_at']

class AIModelLimitedSerializer(serializers.ModelSerializer):
    class Meta:
        model=AIModelInfo
        fields=['id','name','model_id','created_at','description','base_url']
        read_only_fields=['created_at','updated_at']



class ChatSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model=ChatSession
        fields="__all__"