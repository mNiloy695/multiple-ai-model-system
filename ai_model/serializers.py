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


class ChatMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model=ChatMessage
        fields="__all__"

class ChatSessionSerializer(serializers.ModelSerializer):
    messages=ChatMessageSerializer(read_only=True,many=True)
    class Meta:
        model=ChatSession
        fields=['id','model','user','messages','summary']