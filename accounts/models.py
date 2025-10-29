from django.db import models

# Create your models here.

from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
import random
from django.utils import timezone
from datetime import timedelta
from django.utils.text import slugify


class CustomUserManager(BaseUserManager):
    def create_user(self, name, email, prime_phone, password=None, username=None, **extra_fields):
        if not name:
            raise ValueError('Name is required')
        if not email:
            raise ValueError('Email is required')
        if not prime_phone:
            raise ValueError('prime_phone is required')
        
        email = self.normalize_email(email)
        
       
        if not username:
            username = self.generate_unique_username(name)
        
        user = self.model(
            name=name,
            email=email,
            prime_phone=prime_phone,
            username=username,
            **extra_fields
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, name, email, prime_phone, password=None, **extra_fields):
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(name, email, prime_phone, password, user_type='admin', **extra_fields)

    def generate_unique_username(self, email):
        """
        Generate a unique username using the part before '@' in the email.
        If it already exists, append a random 4-digit number.
        """
        base_username = email.split('@')[0]
        base_username = slugify(base_username)  # make sure it’s URL/username-safe

        # Try to find a unique username
        for _ in range(10):
            # Only add random numbers if needed
            username_candidate = f"{base_username}{random.randint(1000, 9999)}" if CustomUser.objects.filter(username=base_username).exists() else base_username

            if not CustomUser.objects.filter(username=username_candidate).exists():
                return username_candidate

        raise ValueError("Unable to generate a unique username. Try again.")

class CustomUser(AbstractBaseUser, PermissionsMixin):
    name = models.CharField(max_length=255)
    username = models.CharField(max_length=255, unique=True, null=True, blank=True)
    email = models.EmailField(unique=True)
    prime_phone = models.CharField(max_length=15, unique=True)
    is_active = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    is_suspended = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)
    last_login = models.DateTimeField(null=True, blank=True)

    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['name', 'prime_phone']

    def save(self, *args, **kwargs):
        # Auto-generate username if not provided
        if not self.username:
            self.username = CustomUserManager().generate_unique_username(self.email)
            if self.user_type == 'admin':
                
                self.is_superuser = True
                self.is_staff = True
            else:
                self.is_superuser = False
                self.is_staff = False
            
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({self.user_type} {self.id})"


class OTP(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='otps')
    code = models.IntegerField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(blank=True, null=True)

    def save(self, *args, **kwargs):
        # Delete expired OTPs
        OTP.objects.filter(expires_at__lt=timezone.now()).delete()
        
        # Generate 4-digit code if not provided
        if not self.code:
            self.code = random.randint(1000, 9999)
        
        # Set expiry if not provided (10 minutes from now)
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(minutes=10)
        
        super().save(*args, **kwargs)

    def is_expired(self):
        return timezone.now() > self.expires_at

    def __str__(self):
        return f"{self.user.email} - {self.code} ({'expired' if self.is_expired() else 'active'})"