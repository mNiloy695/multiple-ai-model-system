from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import ChatMessage
from .summerize import local_summarize

@receiver(post_save, sender=ChatMessage)
def update_session_summary(sender, instance, created, **kwargs):
    if not created:
        return  

    session = instance.session

    messages = session.messages.filter().order_by('-created_at')[:20][::-1]
    combined_text = "\n".join([m.content for m in messages])

    
    from .models import ChatSession
    ChatSession.objects.filter(id=session.id).update(summary=local_summarize(combined_text))
