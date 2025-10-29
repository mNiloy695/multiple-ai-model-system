from rest_framework import serializers
from .models import CustomUser, OTP

class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = CustomUser
        fields = ['id','name','email','prime_phone','username','user_type','password','is_active']
        read_only_fields = ['id','is_active']

    def create(self, validated_data):
        user = CustomUser.objects.create_user(
            name = validated_data['name'],
            email = validated_data['email'],
            prime_phone = validated_data['prime_phone'],
            password = validated_data['password'],
        )
        return user

class OTPVerifySerializer(serializers.Serializer):
    email = serializers.EmailField()
    code = serializers.IntegerField()

class ResetPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()
    code = serializers.IntegerField()
    new_password = serializers.CharField(write_only=True)