from .models import RewardsHistory
from rest_framework import serializers
from django.utils.translation import gettext as _
class RewardsHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model=RewardsHistory
        fields="__all__"
        read_only_fields=["created_at","updated_at"]
    
    def validate(self,attrs):
        reward=attrs.get('reward',0)
        
        if reward<=0:
            raise serializers.ValidationError(_("Reward must be greater than zero"))
        return attrs

    
    
