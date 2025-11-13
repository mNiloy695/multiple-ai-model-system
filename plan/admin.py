from django.contrib import admin
from .models import Revenue,PlanModel,SubscriptionModel

# Register your models here.
@admin.register(Revenue)
class AdminRevenue(admin.ModelAdmin):
    list_display=['id','amount','user__email','payment_id','plan']

@admin.register(PlanModel)
class AdminPlan(admin.ModelAdmin):
    list_display=["name","plan_code","discription","words_or_credits","amount","subscription_duration","created_at","updated_at"]



@admin.register(SubscriptionModel)
class AdminSubscription(admin.ModelAdmin):
    list_display=["plan",'price',"credits_words","used_words","duration_type","start_date","expire_date","status","created_at"]


