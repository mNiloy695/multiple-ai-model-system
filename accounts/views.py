from .google_auth import get_or_create_google_user, generate_jwt_for_user
import requests
from .serializers import RegisterSerializer, UserAccountActivationSerializer
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .utils import send_the_email
from .models import OTP,CreditAccount
from django.contrib.auth import get_user_model
from rest_framework.permissions import IsAuthenticated, AllowAny
from .tasks import send_otp_email_task
from django.utils.translation import gettext as _
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
            send_otp_email_task.delay(subject="Welcome to MultiAI Platform 🚀",user_email=user.email,message=message,message_type='registration')
#             send_otp_email_task.apply_async(
#     args=(),  # if you have only kwargs, leave empty
#     kwargs={
#         "subject": "Welcome to MultiAI Platform 🚀",
#         "user_email": user.email,
#         "message": message,
#         "message_type": "registration"
#     }
# )

            return Response({"message": _("User registered successfully. Please check your email for the verification code.")}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ActivateAccountView(APIView):
    def post(self, request):
        serializer = UserAccountActivationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            user.is_active = True
            user.save()
            
            OTP.objects.filter(user=user, type='registration').delete()
            return Response({"message": _("Account activated successfully.")}, status=status.HTTP_200_OK)
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
                'credits_balance': user.creditaccount.credits if hasattr(user, 'creditaccount') else 0,
                "total_token_used":user.total_token_used
                
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
            return Response({"message": _("User logged out successfully.")}, status=status.HTTP_205_RESET_CONTENT)
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
            return Response({"error": _("Email not found in Google token")}, status=status.HTTP_400_BAD_REQUEST)

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
                    {"error": _("No account found with this email.")},
                    status=status.HTTP_404_NOT_FOUND
                )

            code = randint(100000, 999999)
            OTP.objects.create(user=user, code=code, type='registration')
            
            message = f"Hello! Your temporary code is {code}. It will expire in 10 minutes."
            send_otp_email_task.delay(
                subject="Forgot Password 🚀",
                user_email=email,
                message=message,
                message_type='forgot password'
            )
            return Response({"success": _("OTP sent successfully to your email")}, status=status.HTTP_200_OK)

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
                return Response({"error": _("User not available on this email")}, status=status.HTTP_404_NOT_FOUND)

            otp = OTP.objects.filter(user=user, code=code).first()
            if not otp:
                return Response({"error": _("Invalid OTP")}, status=status.HTTP_400_BAD_REQUEST)
            if otp.is_expired():
                return Response({"error": _("OTP expired")}, status=status.HTTP_400_BAD_REQUEST)

            user.set_password(password)
            if user.is_active == False:
                user.is_active = True
            user.save()
            
            # Delete OTP after successful use
            otp.delete()

            return Response({"success": _("Password reset successfully")}, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)




from rest_framework import viewsets,permissions
from .models import UserProfile
from .serializers import UserProfileSerializer

class CustomerPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.user.is_authenticated:
            return True
        return False
    def has_object_permission(self, request, view, obj):
        return request.user.is_staff or obj.user==request.user

class ProfileView(viewsets.ModelViewSet):
    queryset=UserProfile.objects.select_related('user',"user__creditaccount")
    permission_classes=[CustomerPermission]
    serializer_class=UserProfileSerializer
    

    def create(self, request, *args, **kwargs):
        # Check if user already has a profile
        profile = UserProfile.objects.filter(user=request.user).first()
        if profile:
            # If profile exists, update it instead of creating a new one
            serializer = self.get_serializer(profile, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            first_name=request.data.get("first_name",None)
            last_name=request.data.get("last_name",None)
            if first_name:
                request.user.first_name=first_name
            if last_name:
                request.user.last_name=last_name
            request.user.save(update_fields=['first_name','last_name'])
            self.perform_update(serializer)
            return Response(serializer.data, status=status.HTTP_200_OK)
        return super().create(request, *args, **kwargs)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    # def get_queryset(self):
    #     if self.request.user.is_staff:
    #         return super().get_queryset()
    #     return super().get_queryset().filter(user=self.request.user)

    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.filter(user=self.request.user)

        # Non-staff users only see their own profile
        # if not self.request.user.is_staff:
        #     queryset = queryset.filter(user=self.request.user)

        # 🔍 Filter by email (query param)
        email = self.request.query_params.get("email")
        if email:
            queryset = queryset.filter(user__email__icontains=email)

        return queryset
    





#Credit Account View

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import CreditAccount
from .serializers import CreditAccountSerializer
from rest_framework.permissions import IsAuthenticated



class CreditAccountView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        try:
            credit_account = CreditAccount.objects.get(user=request.user)
            serializer = CreditAccountSerializer(credit_account)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except CreditAccount.DoesNotExist:
            return Response({"error": _("Credit account not found.")}, status=status.HTTP_404_NOT_FOUND)








#Apple Login and Registration 

import requests

import jwt
from .apple_auth import get_or_create_apple_user

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
import jwt, requests
from django.conf import settings

APPLE_KEYS_URL = "https://appleid.apple.com/auth/keys"

@api_view(["POST"])
def apple_login(request):
    identity_token = request.data.get("identity_token")

    if not identity_token:
        return Response(
            {"error": "identity_token is required"},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
      
        keys = requests.get(APPLE_KEYS_URL).json()["keys"]

        
        header = jwt.get_unverified_header(identity_token)
        
        key = next(k for k in keys if k["kid"] == header["kid"])

        
        public_key = jwt.algorithms.RSAAlgorithm.from_jwk(key)

        
        payload = jwt.decode(
            identity_token,
            public_key,
            algorithms=["RS256"],
            audience=settings.APPLE_CLIENT_ID,
            issuer="https://appleid.apple.com",
        )

       
        user = get_or_create_apple_user(payload)
        tokens = generate_jwt_for_user(user=user)

        return Response(tokens, status=status.HTTP_200_OK)

    except jwt.ExpiredSignatureError:
        return Response(
            {"error": "Token expired"},
            status=status.HTTP_401_UNAUTHORIZED
        )

    except jwt.InvalidAudienceError:
        return Response(
            {"error": "Invalid audience"},
            status=status.HTTP_401_UNAUTHORIZED
        )

    except jwt.InvalidIssuerError:
        return Response(
            {"error": "Invalid issuer"},
            status=status.HTTP_401_UNAUTHORIZED
        )

    except jwt.InvalidTokenError:
        return Response(
            {"error": "Invalid Apple token"},
            status=status.HTTP_401_UNAUTHORIZED
        )

    except Exception as e:
        return Response(
            {"error": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
