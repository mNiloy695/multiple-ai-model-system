from django.contrib.auth import get_user_model
User=get_user_model()

def get_or_create_apple_user(apple_data):
   
    email = apple_data.get("email")


    try:
        user = User.objects.get(email=email)
        return user

    except User.DoesNotExist:
        

        user, created = User.objects.get_or_create(
        email=email,
        defaults={
    
            "username": email,  # optional
            # "password": User.objects.make_random_password()  # random password for JWT
        }
    )

        user.set_unusable_password()
        user.is_active = True
        user.save()
        return user