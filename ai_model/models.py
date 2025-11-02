from django.db import models


class AIModelInfo(models.Model):

    PROVIDER_CHOICES = [
        ('openai', 'OpenAI'),
        ('huggingface', 'Hugging Face'),
        ('anthropic', 'Anthropic'),
        ('google', 'Google DeepMind'),
        ('mistral', 'Mistral AI'),
        ('meta', 'Meta AI'),
        ('custom', 'Custom / Self-Hosted'),
    ]

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
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


    def __str__(self):
        return f"{self.name} (v{self.version}) — {self.provider}"


from django.contrib.auth import get_user_model

User= get_user_model()

class ChatSession(models.Model):
    model = models.ForeignKey(AIModelInfo, on_delete=models.CASCADE, related_name='chat_sessions')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chat_sessions')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Session: {self.id} using {self.model.name}"

class ChatMessage(models.Model):
    session = models.ForeignKey(ChatSession, on_delete=models.CASCADE, related_name='messages')
    sender = models.CharField(max_length=50, choices=[('user', 'User'), ('ai', 'AI Model')])
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Message from {self.sender} at {self.created_at}"




