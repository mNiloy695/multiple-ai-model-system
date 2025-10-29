from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken,TokenError
from .models import CustomUser, OTP
from .serializers import UserSerializer, OTPVerifySerializer, ResetPasswordSerializer
from django.utils import timezone
import random
from .tasks import send_otp_email_task
from django.conf import settings
from .utils import get_avatar_url, send_otp_email


# ✅ Register
class RegisterAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            # generate and send OTP
            otp = OTP.objects.create(user=user, code=random.randint(1000,9999))
            send_otp_email_task.delay(user.email, otp.code, user.name, task="Account Verification")
            return Response({"message":"OTP sent. Verify to activate account."}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# ✅ Verify OTP
class VerifyOTPAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = OTPVerifySerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            code = serializer.validated_data['code']
            try:
                otp_obj = OTP.objects.get(user__email=email, code=code)
                if otp_obj.is_expired():
                    return Response({"error":"OTP expired"}, status=status.HTTP_400_BAD_REQUEST)
                user = otp_obj.user
                user.is_active = True
                user.save()
                otp_obj.delete()
                return Response({"message":"Account verified successfully"}, status=status.HTTP_200_OK)
            except OTP.DoesNotExist:
                return Response({"error":"Invalid OTP or email"}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class ResendOTPAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get("email")
        try:
            user = CustomUser.objects.get(email=email)
            if user.is_active:
                return Response({"error":"Account already verified"}, status=status.HTTP_400_BAD_REQUEST)
            otp_obj_delete= OTP.objects.filter(user=user)
            otp_obj_delete.delete()
            otp_obj = OTP.objects.create(user=user, code=random.randint(1000,9999))
            send_otp_email_task.delay(user.email, otp_obj.code, user.name, task="Account Verification")
            return Response({"message":"OTP resent successfully"}, status=status.HTTP_200_OK)
        except CustomUser.DoesNotExist:
            return Response({"error":"User not found"}, status=status.HTTP_404_NOT_FOUND)

# ✅ Login
from django.middleware import csrf
class LoginAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get("email")
        password = request.data.get("password")

        user = authenticate(request, email=email, password=password)
        print(CustomUser.objects.filter(email=email))
       #print(user)
        if user:
            if not user.is_active:
                return Response({"error":"Account not verified"}, status=status.HTTP_403_FORBIDDEN)
            refresh = RefreshToken.for_user(user)
            user.last_login = timezone.now()
            user.save()
            user_data = UserSerializer(user).data
            user_data['avatar_url'] = get_avatar_url(user, request)
            return Response({
                "refresh": str(refresh),
                "access": str(refresh.access_token),
                "user": user_data,
                "message": "Login successful"
            }, status=status.HTTP_200_OK)
            # refresh = RefreshToken.for_user(user)
            # access_token = str(refresh.access_token)
            # response = Response({"message": "Login successful" , 
            #                      'user': UserSerializer(user).data,
                                 
                                 
            #                      })
            # response.set_cookie(
            #  key="access_token",
            # value=str(refresh.access_token),
            # httponly=True,
            # samesite='None',
            # secure=True,
            # max_age=5 * 60,  # 5 minutes
            # )
            # response.set_cookie(
            #      key="refresh_token",
            # value=str(refresh),
            # httponly=True,
            # samesite='Lax',
            # secure=True,
            # max_age=7 * 24 * 60 * 60,  # 7 days
            # )

            # csrf_token = csrf.get_token(request)
            # response.set_cookie("csrftoken", csrf_token)
            # response.data = {"message": "Login successful", "csrfToken": csrf_token}
            #return response
            
        
        return Response({"error":"Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)

# ✅ Forget Password
class ForgetPasswordAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get("email")
        try:
            user = CustomUser.objects.get(email=email)
            otp_obj = OTP.objects.create(user=user, code=random.randint(1000,9999))
            send_otp_email_task.delay(user.email,otp_obj.code,user.name)
            return Response({"message":"OTP sent to reset password"}, status=status.HTTP_200_OK)
        except CustomUser.DoesNotExist:
            return Response({"error":"User not found"}, status=status.HTTP_404_NOT_FOUND)

# ✅ Reset Password
class ResetPasswordAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            code = serializer.validated_data['code']
            new_password = serializer.validated_data['new_password']
            try:
                otp_obj = OTP.objects.get(user__email=email, code=code)
                if otp_obj.is_expired():
                    return Response({"error":"OTP expired"}, status=status.HTTP_400_BAD_REQUEST)
                user = otp_obj.user
                user.set_password(new_password)
                user.save()
                otp_obj.delete()
                return Response({"message":"Password reset successfully"}, status=status.HTTP_200_OK)
            except OTP.DoesNotExist:
                return Response({"error":"Invalid OTP or email"}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data.get("refresh")
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({"detail": "Successfully logged out."}, status=status.HTTP_205_RESET_CONTENT)
        except TokenError:
            return Response({"detail": "Invalid or expired token."}, status=status.HTTP_400_BAD_REQUEST)