from rest_framework import serializers
from .models import AIModelInfo,ChatMessage,ChatSession

class AIModelSerializer(serializers.ModelSerializer):
    class Meta:
        model=AIModelInfo
        fields='__all__'
        read_only_fields=['created_at','updated_at']
    
    def validate(self, attrs):
        images_generating_models=attrs.get('images_generating_models',False)
        base_cost=attrs.get('base_cost',None)

        if images_generating_models and (base_cost is None or base_cost<=0):
            raise serializers.ValidationError("Base cost must be greater than 0 for image generating models.")
        return attrs

class AIModelLimitedSerializer(serializers.ModelSerializer):
    class Meta:
        model=AIModelInfo
        fields=['id','name','model_id','created_at','description','base_url','base_cost','images_generating_models']
        read_only_fields=['created_at','updated_at']



class ChatMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model=ChatMessage
        fields="__all__"

class ChatSessionSerializer(serializers.ModelSerializer):
    messages=ChatMessageSerializer(read_only=True,many=True)
    text = serializers.BooleanField(write_only=True,required=False,help_text="Indicates if the session is for text or image generation.")
    class Meta:
        model=ChatSession
        fields=['id','model','user','messages','summary','text','created_at','updated_at']
        read_only_fields=['created_at','updated_at','user','messages']