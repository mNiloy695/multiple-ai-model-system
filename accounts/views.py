from .serializers import RegisterSerializer, UserAccountActivationSerializer
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .utils import send_the_email
from .models import OTP
from django.contrib.auth import get_user_model
from rest_framework.permissions import IsAuthenticated, AllowAny
from .tasks import send_otp_email_task
User= get_user_model()
from random import randint
class RegisterView(APIView):
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            user.is_active = False
            user.save()
            code = randint(100000,999999)
            OTP.objects.create(user=user, code=code, type='registration')
            message = f"Hello {user.username}\n\n Your verification code is: {code} ! It will expire in 10 minutes.\n\nThank you for registering with us!\n\nBest regards,\nMultiAI Platform Team"
            send_the_email(subject="Welcome to MultiAI Platform 🚀",user_email=user.email,message=message,message_type='registration')
            return Response({"message": "User registered successfully. Please check your email for the verification code."}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ActivateAccountView(APIView):
    def post(self, request):
        serializer = UserAccountActivationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            user.is_active = True
            user.save()
            
            OTP.objects.filter(user=user, type='registration').delete()
            return Response({"message": "Account activated successfully."}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

from .serializers import LoginSerializer
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
class LoginView(APIView):
    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user=serializer.validated_data['user']
            
            refresh = RefreshToken.for_user(user)
            return Response({
                'user':{
                    'user_id': user.id,
                'email': user.email,
                'username': user.username,
                'is_active': user.is_active,
                'is_staff': user.is_staff,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'credits_balance': user.creditaccount.credits if hasattr(user, 'creditaccount') else 0
                
                },
                
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

class LogoutView(APIView):
    # permission_classes = [IsAuthenticated]
    def post(self, request):
        try:
            refresh_token = request.data["refresh"]
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({"message": "User logged out successfully."}, status=status.HTTP_205_RESET_CONTENT)
        except Exception as e:
            return Response({"error": "Invalid token."}, status=status.HTTP_400_BAD_REQUEST)






#Transection History View

from .models import CreditTransaction
from .serializers import CreditTransactionSerializer
from rest_framework.generics import ListAPIView

class CreditTransactionHistoryView(ListAPIView):
    serializer_class = CreditTransactionSerializer
    permission_classes = [IsAuthenticated]
    def get_queryset(self):
        user = self.request.user
        if not user.is_staff:
            return CreditTransaction.objects.select_related('credit_account').filter(credit_account__user=user).order_by('-created_at')
        return CreditTransaction.objects.select_related('credit_account').all().order_by('-created_at')
            