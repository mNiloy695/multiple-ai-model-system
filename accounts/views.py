from .google_auth import get_or_create_google_user, generate_jwt_for_user
import requests
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
                'subscribed':user.subscribed,
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



#views for google authentication 

from .google_auth import get_or_create_google_user, generate_jwt_for_user
import requests

class GoogleLoginAPIView(APIView):
    """
    Receives Google id_token from frontend and returns JWT tokens.
    """
    def post(self, request):
        id_token = request.data.get("id_token")
        if not id_token:
            return Response({"error": "No token provided"}, status=status.HTTP_400_BAD_REQUEST)

        # Verify token with Google
        google_response = requests.get(f"https://oauth2.googleapis.com/tokeninfo?id_token={id_token}")
        if google_response.status_code != 200:
            return Response({"error": "Invalid Google token"}, status=status.HTTP_400_BAD_REQUEST)

        google_data = google_response.json()
        email = google_data.get("email")
        if not email:
            return Response({"error": "Email not found in Google token"}, status=status.HTTP_400_BAD_REQUEST)

        # Get or create user
        user = get_or_create_google_user(google_data)

        # Generate JWT
        tokens = generate_jwt_for_user(user)

        return Response(tokens, status=status.HTTP_200_OK)




#forgot password 

from .serializers import ForgotPasswordSerializer
from django.shortcuts import get_object_or_404

class ForgotPasswordView(APIView):
    def post(self, request, *args, **kwargs):
        serializer = ForgotPasswordSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                return Response(
                    {"error": "No account found with this email."},
                    status=status.HTTP_404_NOT_FOUND
                )

            code = randint(100000, 999999)
            OTP.objects.create(user=user, code=code, type='registration')
            
            message = f"Hello! Your temporary code is {code}. It will expire in 10 minutes."
            send_the_email(
                subject="Forgot Password 🚀",
                user_email=email,
                message=message,
                message_type='forgot password'
            )
            return Response({"success": "OTP sent successfully to your email"}, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        

from .serializers import ResetPasswordSerializer

class ResetView(APIView):
    def post(self, request, *args, **kwargs):
        serializer = ResetPasswordSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            code = serializer.validated_data['code']
            password = serializer.validated_data['password']

            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                return Response({"error": "User not available on this email"}, status=status.HTTP_404_NOT_FOUND)

            otp = OTP.objects.filter(user=user, code=code).first()
            if not otp:
                return Response({"error": "Invalid OTP"}, status=status.HTTP_400_BAD_REQUEST)

            if otp.is_expired():
                return Response({"error": "OTP expired"}, status=status.HTTP_400_BAD_REQUEST)

            user.set_password(password)
            user.save()
            
            # Delete OTP after successful use
            otp.delete()

            return Response({"success": "Password reset successfully"}, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

