from django.db import models
from django.contrib.auth import get_user_model
User = get_user_model()
# Create your models here.

class PlanModel(models.Model):
    name=models.CharField(null=True,blank=True)
    stripe_product_price_id=models.CharField(null=True,blank=True)
    plan_code=models.CharField(unique=True)
    discription=models.TextField(blank=True,null=True)
    words_or_credits=models.IntegerField(help_text="how much word will be added in user credits ?")
    amount=models.FloatField(default=0)
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at=models.DateTimeField(auto_now=True)


class Revenue(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)  
    plan = models.ForeignKey('PlanModel', on_delete=models.SET_NULL, null=True, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_id = models.CharField(max_length=100, null=True, blank=True)  
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at=models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user} - {self.amount} on {self.created_at}"
