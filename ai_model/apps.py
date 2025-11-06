from django.apps import AppConfig


class AiModelConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'ai_model'
    def ready(self):
        import ai_model.signals 
