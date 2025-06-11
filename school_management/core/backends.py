from django.contrib.auth.backends import ModelBackend
from django.db import models  # Add this import
from .models import User  # Make sure to import your User model

class MultiAuthBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        try:
            # Try to find user by username or email
            user = User.objects.get(
                models.Q(username=username) | 
                models.Q(email=username)
            )
            if user.check_password(password) and self.user_can_authenticate(user):
                return user
        except User.DoesNotExist:
            return None

    def user_can_authenticate(self, user):
        # Only allow approved users to login (except admins)
        return user.is_approved or user.is_superuser