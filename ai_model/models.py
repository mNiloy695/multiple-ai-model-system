from django.db import models
from django.conf import settings

User = settings.AUTH_USER_MODEL


class AIModel(models.Model):
    name = models.CharField(max_length=100, unique=True)
    provider = models.CharField(max_length=50)
    model_id = models.CharField(max_length=100)
    api_key = models.CharField(max_length=255, blank=True, null=True)
    base_url = models.URLField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.name} ({self.provider})"


class ChatSession(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="chat_sessions")
    model = models.ForeignKey(AIModel, on_delete=models.SET_NULL, null=True, related_name="sessions")
    title = models.CharField(max_length=255, default="New Chat")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_pinned = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.title} ({self.user})"


class ChatMessage(models.Model):
    session = models.ForeignKey(ChatSession, on_delete=models.CASCADE, related_name="messages")
    sender = models.CharField(max_length=10, choices=[('user', 'User'), ('ai', 'AI')])
    content = models.TextField()
    model_used = models.ForeignKey(AIModel, on_delete=models.SET_NULL, null=True, related_name="messages")
    token_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)


class SessionMemory(models.Model):
    session = models.OneToOneField(ChatSession, on_delete=models.CASCADE, related_name="memory")
    summary = models.TextField(blank=True, null=True)
    last_updated = models.DateTimeField(auto_now=True)


class UserCredit(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="credit")
    total_credits = models.IntegerField(default=0)
    used_credits = models.IntegerField(default=0)


class CreditTransaction(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    type = models.CharField(max_length=20, choices=[('purchase','Purchase'),('subscription','Subscription'),('usage','Usage')])
    amount = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)


class SubscriptionPlan(models.Model):
    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    credits_per_month = models.IntegerField()
    interval = models.CharField(max_length=20, default='monthly')
    description = models.TextField(blank=True, null=True)
    stripe_price_id = models.CharField(max_length=200, blank=True, null=True)

class UserSubscription(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="subscriptions")
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.SET_NULL, null=True)
    status = models.CharField(max_length=20, choices=[('active','Active'),('canceled','Canceled'),('expired','Expired'),('pending','Pending')], default='pending')
    start_date = models.DateTimeField(auto_now_add=True)
    end_date = models.DateTimeField(null=True, blank=True)
    auto_renew = models.BooleanField(default=True)
    stripe_subscription_id = models.CharField(max_length=200, blank=True, null=True)
    last_renewal = models.DateTimeField(auto_now_add=True)
    
