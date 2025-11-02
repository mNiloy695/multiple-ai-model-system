from rest_framework import serializers
from django.contrib.auth import get_user_model
User=get_user_model()

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)
    class Meta:
        model = User
        fields = ['id','username','email','password','first_name','last_name','is_staff','confirm_password']

    def validate(self, attrs):
        password=  attrs.get('password')
        confirm_password= attrs.get('confirm_password')
        if password is None or confirm_password is None:
            raise serializers.ValidationError("Password and Confirm Password are required")
        if password != confirm_password:
            raise serializers.ValidationError("Password and Confirm Password does not match")
        username=attrs.get('username')
        if username is None:
            raise serializers.ValidationError("Username is required")
        
        # if len(password) < 8:
        #     raise serializers.ValidationError("Password must be at least 8 characters long")
        email= attrs.get('email')

        if User.objects.filter(email=email).exists():
            raise serializers.ValidationError("Email is already in use")
        if User.objects.filter(username=attrs.get('username')).exists():
            raise serializers.ValidationError("Username is already in use")
                
        
        return attrs
    
    def create(self, validated_data):
        validated_data.pop('confirm_password')
        user= User.objects.create_user(**validated_data)
        return user 



#active the user account 

class UserAccountActivationSerializer(serializers.Serializer):
    email= serializers.EmailField()
    code= serializers.CharField(max_length=6)
    def validate(self, attrs):
        email= attrs.get('email')
        code= attrs.get('code')
        try:
            user= User.objects.get(email=email)
        except User.DoesNotExist:
            raise serializers.ValidationError("User with this email does not exist")
        
        from .models import OTP
        if not OTP.objects.filter(user=user, code=code, type='registration').exists():
            raise serializers.ValidationError("Invalid verification code")
        else:
            otp= OTP.objects.get(user=user, code=code, type='registration')
            if otp.is_expired():
                raise serializers.ValidationError("Verification code has expired")
        
        attrs['user']= user
        return attrs


class LoginSerializer(serializers.Serializer):
    email= serializers.EmailField()
    password= serializers.CharField(write_only=True)

    def validate(self, attrs):
        email= attrs.get('email')
        password= attrs.get('password')
        try:
            user= User.objects.get(email=email)
        except User.DoesNotExist:
            raise serializers.ValidationError("Invalid email or password")
        
        if not user.check_password(password):
            raise serializers.ValidationError("Invalid email or password")
        
        if not user.is_active:
            raise serializers.ValidationError("Account is not activated")
        
        attrs['user']= user
        return attrs
    


# this site for Credit Account Serializer
from .models import CreditTransaction
class CreditTransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = CreditTransaction
        fields = ['id', 'amount', 'transaction_type', 'message', 'created_at']