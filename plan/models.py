from django.db import models
# Create your models here.

class PlanModel(models.Model):
    name=models.CharField(null=True,blank=True)
    stripe_product_price_id=models.CharField(null=True,blank=True)
    plan_code=models.CharField(unique=True)
    discription=models.TextField(blank=True,null=True)
    words_or_credits=models.IntegerField(help_text="how much word will be added in user credits ?")
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at=models.DateTimeField(auto_now=True)
