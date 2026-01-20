from django.contrib import admin
from unfold.admin import ModelAdmin
from .models import Revenue,PlanModel #,SubscriptionModel

# Register your models here.
@admin.register(Revenue)
class AdminRevenue(ModelAdmin):
    list_display=['id','amount','user__email','payment_id','plan']
    list_per_page=20

@admin.register(PlanModel)
class AdminPlan(ModelAdmin):
    list_display=["name","plan_code","discription","words_or_credits","amount","created_at","updated_at"]
    list_per_page=20



# @admin.register(SubscriptionModel)
# class AdminSubscription(admin.ModelAdmin):
#     list_display=["plan",'price',"credits_words","used_words","duration_type","start_date","expire_date","status","created_at"]


