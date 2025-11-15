from .models import PlanModel,SubscriptionModel
from rest_framework import serializers

class PlanSerializer(serializers.ModelSerializer):
    class Meta:
        model=PlanModel
        fields="__all__"

class SubscriptionSerializer(serializers.ModelSerializer):
    user_details=serializers.SerializerMethodField(read_only=True)
    plan_details=serializers.SerializerMethodField(read_only=True)
    class Meta:
        model=SubscriptionModel
        fields=["plan","user","price","credits_words","duration_type","used_words","start_date","expire_date","status","created_at","updated_at","user_details","plan_details"]
    
    def get_user_details(self,obj):
        user=obj.user
        return {
            'id':user.id,
            "username":user.username,
            "email":user.email
        }
    
    def get_plan_details(self,obj):
        plan=obj.plan
        return {
            'id':plan.id,
            'plan_code':plan.plan_code,
            "words_or_credits":plan.words_or_credits,
            "amount":plan.amount,
            "subscription_duration":plan.subscription_duration
        }