from django.db import models


class AIModelInfo(models.Model):

    PROVIDER_CHOICES = [
        ('openai', 'OpenAI'),
        # ('leonardo', 'Leonardo AI'),
        ('wavespeedai','Wavespeed AI'),
        # ('huggingface', 'Hugging Face'),
        # ('anthropic', 'Anthropic'),
        ('google', 'Google'),
        ('deepseek','deepseek'),
        # ('falai', 'FAL AI'),
        # ('mistral', 'Mistral AI'),
        # ('meta', 'Meta AI'),
        # ('custom', 'Custom / Self-Hosted'),
    ]
    MODEL=(
        ('chat','chat'),
        ('image_editor','image_editor'),
       ('text_to_image','text_to_image'),
        ('image_to_video','image_to_video'),
        ('text_to_video','text_to_video'),
        ('text_or_image_to_video','text_or_image_to_video'),
        ('image_tool','image_tool'),
        # ('image_upscaler','image_upscaler'),
        ('video_upscaler','video_upscaler'),
        ('image_to_3d','image_to_3d'),
        ('video_effect','video_effect'),
        ('text_to_speech','text_to_speech'),
    )
    image=models.ImageField(upload_to='media/profile/',null=True,blank=True)
    logo=models.ImageField(upload_to='media/logo/',null=True,blank=True)
    name = models.CharField(max_length=255, help_text="Name of the AI model, e.g., GPT-4 or Claude 3.")
    version = models.CharField(max_length=50, help_text="Version or build identifier of the model.")
    provider = models.CharField(max_length=50, choices=PROVIDER_CHOICES, help_text="Model provider or vendor.")
    model_id = models.CharField(max_length=255, help_text="Unique identifier for the model within the provider's ecosystem.", unique=True)
    api_key = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="API key for accessing this model from the provider."
    )
    base_url = models.URLField(
        max_length=255,
        blank=True,
        null=True,
        help_text="endpoint URL (for self-hosted or experimental models)."
    )
    description = models.TextField(blank=True,null=True,help_text="Brief description of the model’s purpose or usage context.")
    is_active = models.BooleanField(default=True, help_text="Indicates if the model is currently available for use.")
    model_type=models.CharField(choices=MODEL,max_length=50,null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    # images_generating_models=models.BooleanField(default=False,help_text="Indicates if the model supports image generation")
    base_cost=models.DecimalField(default=0,help_text="base cost in terms of words or credits for using this model",decimal_places=50,max_digits=100)


    def __str__(self):
        return f"{self.name} (v{self.version}) — {self.provider}"


from django.contrib.auth import get_user_model

User= get_user_model()


Session_Type=(
        ('chat','chat'),
        ('image_editor','image_editor'),
       ('text_to_image','text_to_image'),
        ('image_to_video','image_to_video'),
        ('text_to_video','text_to_video'),
        ('image_tool','image_tool'),
        ('text_or_image_to_video','text_or_image_to_video'),
        # ('image_upscaler','image_upscaler'),
        ('video_upscaler','video_upscaler'),
        ('image_to_3d','image_to_3d'),
        ('video_effect','video_effect'),
        ('text_to_speech','text_to_speech'),
       
        
    )
class ChatSession(models.Model):
    model = models.ForeignKey(AIModelInfo, on_delete=models.SET_NULL,blank=True,null=True,related_name='chat_sessions')
    user = models.ForeignKey(User, on_delete=models.CASCADE,blank=True, related_name='chat_sessions')
    summary=models.TextField(null=True,blank=True)
    session_type=models.CharField(choices=Session_Type,max_length=50,null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        ordering=['-updated_at']
 

class ChatMessage(models.Model):
    session = models.ForeignKey(ChatSession, on_delete=models.CASCADE, related_name='messages')
    sender = models.CharField(max_length=50, choices=[('user', 'User'), ('ai', 'AI Model')])
    images = models.JSONField(default=list, blank=True)
    voice = models.FileField(upload_to='media/voice_chat/', null=True, blank=True)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    def __str__(self):
        return f"Message from {self.sender} at {self.created_at}"




