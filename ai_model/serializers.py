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
        fields=['id','name','model_id','created_at','description','base_url','base_cost','model_type','provider']
        read_only_fields=['created_at','updated_at']

class AIModelPublicSerializer(serializers.ModelSerializer):
    """Serializer for AI model info without exposing sensitive data like API keys"""
    class Meta:
        model = AIModelInfo
        fields = ['id', 'name', 'model_id', 'description', 'provider', 'model_type', 'base_cost']
        read_only_fields = fields


class ChatMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model=ChatMessage
        fields="__all__"

# class ChatSessionSerializer(serializers.ModelSerializer):
#     messages = ChatMessageSerializer(read_only=True, many=True)
#     model = AIModelPublicSerializer(read_only=True)
#     model_id = serializers.PrimaryKeyRelatedField(
#         queryset=AIModelInfo.objects.all(),
#         source='model',
#         write_only=True,
#         required=False
#     )
#     text = serializers.BooleanField(write_only=True, required=False, help_text="Indicates if the session is for text or image generation.")
    
#     class Meta:
#         model = ChatSession
#         fields = ['id', 'model', 'model_id', 'user', 'messages', 'summary', 'text', 'created_at', 'updated_at', 'session_type']
#         read_only_fields = ['created_at', 'updated_at', 'user', 'messages']
    
#     def validate(self, attrs):
        
#         # Creating a new session
#         if not self.instance:
#             session_type = attrs.get('session_type', None)
#             if not session_type:
#                 raise serializers.ValidationError({"error": "Session type is required"})
            
#             # Get model object (PrimaryKeyRelatedField converts ID to object)
#             model = attrs.get('model', None)
#             if not model:
#                raise serializers.ValidationError({"error": "Model field is required"})
#             try:
#                 model=AIModelInfo.objects.get(id=model)
#             except AIModelInfo.DoesNotExist:
#                 raise serializers.ValidationError({"error":"AI model not exist"})
#             # Ensure model object is valid
#             if not hasattr(model, 'model_type'):
#                 raise serializers.ValidationError({"error": "Invalid model"})
            
#             # Check compatibility
#             if not self._is_compatible(model.model_type, session_type):
#                raise serializers.ValidationError({"error": "Model type and Session type must be compatible"})
        
#         # Updating an existing session
#         if self.instance:
#             session_type = attrs.get('session_type', None)
#             model = attrs.get('model', None)  # This is the model object, not ID
            
#             try:
#                 model=AIModelInfo.objects.get(id=model)
#             except AIModelInfo.DoesNotExist:
#                 raise serializers.ValidationError({"error":"AI model not exist"})
            
#             # Only validate if both fields are being updated
#             if model and session_type:
#                 if hasattr(model, 'model_type'):
#                     if not self._is_compatible(model.model_type, session_type):
#                         raise serializers.ValidationError({"error": "Model type and Session type must be compatible"})
            
#             # If only model is being updated, validate against existing session_type
#             elif model and not session_type:
#                 if hasattr(model, 'model_type') and self.instance.session_type:
#                     if not self._is_compatible(model.model_type, self.instance.session_type):
#                         raise serializers.ValidationError({"error": "Model type must be compatible with existing session type"})
            
#             # If only session_type is being updated, validate against existing model
#             elif session_type and not model:
#                 if self.instance.model and hasattr(self.instance.model, 'model_type'):
#                     if not self._is_compatible(self.instance.model.model_type, session_type):
#                         raise serializers.ValidationError({"error": "Session type must be compatible with existing model type"})

#         return attrs
    
#     def _is_compatible(self, model_type, session_type):
#         """Check if model_type and session_type are compatible"""
#         # Exact match
#         if model_type == session_type:
#             return True
        
#         # text_or_image_to_video models support both text_to_video and image_to_video
#         if model_type == "text_or_image_to_video":
#             return session_type in ["text_to_video", "image_to_video", "text_or_image_to_video"]
        
#         return False

class ChatSessionSerializer(serializers.ModelSerializer):
    messages = ChatMessageSerializer(read_only=True, many=True)

    model = serializers.PrimaryKeyRelatedField(
        queryset=AIModelInfo.objects.all()
    )
    model_name=serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = ChatSession
        fields = [
            'id',
            'model',
            'model_name',
            'user',
            'messages',
            'summary',
            'session_type',
            'created_at',
            'updated_at',
            
            
        ]
        read_only_fields = [
            'id',
            'created_at',
            'updated_at',
            'user',
            'messages',
            'model_name'
        ]

    def validate(self, attrs):
        model = attrs.get('model')          # AIModelInfo instance
        session_type = attrs.get('session_type')

        if not model:
            raise serializers.ValidationError(
                {"model": "Model is required."}
            )

        if not session_type:
            raise serializers.ValidationError(
                {"session_type": "Session type is required."}
            )

        if not self._is_compatible(model.model_type, session_type):
            raise serializers.ValidationError(
                {"error": "Model type and session type must be compatible."}
            )

        return attrs

    def _is_compatible(self, model_type, session_type):
        if model_type == session_type:
            return True

        if model_type == "text_or_image_to_video":
            return session_type in [
                "text_to_video",
                "image_to_video",
                "text_or_image_to_video",
            ]

        return False
    def get_model_name(self, obj):
        return obj.model.name if obj.model else None
