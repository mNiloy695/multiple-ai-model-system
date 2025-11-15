
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.response import Response
from rest_framework import status


User = get_user_model()

def get_or_create_google_user(google_data):
    """
    google_data: dict returned from Google token verification
    """
    email = google_data.get("email")
    first_name = google_data.get("given_name", "")
    last_name = google_data.get("family_name", "")

    # Check if user exists
    user, created = User.objects.get_or_create(
        email=email,
        defaults={
            "first_name": first_name,
            "last_name": last_name,
            "username": email,  # optional
            # "password": User.objects.make_random_password()  # random password for JWT
        }
    )

    return user

def generate_jwt_for_user(user):
    refresh = RefreshToken.for_user(user)
    return{
                'user':{
                    'user_id': user.id,
                'email': user.email,
                'username': user.username,
                'is_active': user.is_active,
                'is_staff': user.is_staff,
                'subscribed':user.subscribed,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'credits_balance': user.creditaccount.credits if hasattr(user, 'creditaccount') else 0,
                "total_token_used":user.total_token_used
                
                },
                
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }
   
