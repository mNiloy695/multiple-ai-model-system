from django.db import models
from django.contrib.auth import get_user_model
from datetime import datetime,timezone
User = get_user_model()
# Create your models here.

PLAN_DURATION=(
    ('weekly','weekly'),
    ('monthly','monthly'),
    ('yearly','yearly'),
    ('one-time','one-time')
)

class PlanModel(models.Model):
    name=models.CharField(null=True,blank=True)
    stripe_product_price_id=models.CharField(null=True,blank=True)
    plan_code=models.CharField(unique=True)
    discription=models.TextField(blank=True,null=True)
    words_or_credits=models.IntegerField(help_text="how much word will be added in user credits ?")
    amount=models.FloatField(default=0)
    subscription_duration=models.CharField(choices=PLAN_DURATION,null=True)
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at=models.DateTimeField(auto_now=True)
    
    
    def __str__(self):
        return f'{self.name} {self.plan_code}'
  
SUBSCRIPTION_STATUS=(
    ('inactive','inactive'),
    ('active','active'),
    ('expired','expired'),
    # ('one-time','one-time'),
)

SUBSCRIPTION_DURATION=(
    ('weekly','weekly'),
    ('monthly','monthly'),
    ('yearly','yearly'),
)
class SubscriptionModel(models.Model):
    plan=models.ForeignKey(PlanModel,related_name='plan_subscription',on_delete=models.SET_NULL,null=True)
    user=models.ForeignKey(User,on_delete=models.CASCADE,null=True,related_name='subscriptions')
    price=models.IntegerField()
    credits_words=models.IntegerField()
    used_words=models.IntegerField()
    duration_type=models.CharField(choices=SUBSCRIPTION_DURATION)
    start_date=models.DateField()
    expire_date=models.DateField()
    status=models.CharField(choices=SUBSCRIPTION_STATUS,null=True,default="active")
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at=models.DateTimeField(auto_now=True)

    @property
    def is_expired(self):
        return self.expire_date<datetime.now(timezone.utc)
    
    
    
    
   



class Revenue(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)  
    plan = models.ForeignKey('PlanModel', on_delete=models.SET_NULL, null=True, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_id = models.CharField(max_length=100, null=True, blank=True)  
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at=models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user} - {self.amount} on {self.created_at}"
