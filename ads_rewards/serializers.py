from .models import RewardsHistory
from rest_framework import serializers
class RewardsHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model=RewardsHistory
        fields="__all__"
        read_only_fields=["created_at","updated_at"]
    
    def validate(self,attrs):
        reward=attrs.get('reward',0)
        
        if reward<=0:
            raise serializers.ValidationError("Reward must be grater than zero")
        return attrs

    
    
