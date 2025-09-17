from base_app.models import *
import jwt
from django.utils import timezone

def generate_custom_tokens(user):
    """ Generates custom JWT access & refresh tokens without expiry """
    
    # Create access token (NO EXPIRY)
    access_token_payload = {
        "user_id": user.id,
        "user_name": user.user_name,
        "iat": timezone.now().timestamp(),  # FIXED: Added () and converted to timestamp
        "token_type": "access"
    }
    access_token = jwt.encode(access_token_payload, "MagaIgnyte", algorithm="HS256")

    # Create refresh token (NO EXPIRY)
    refresh_token_payload = {
        "user_id": user.id,
        "iat": timezone.now().timestamp(),  # FIXED: Added () and converted to timestamp
        "token_type": "refresh"
    }
    refresh_token = jwt.encode(refresh_token_payload, "MagaIgnyte", algorithm="HS256")

    # Save tokens to the database
    UserToken.objects.update_or_create(
        user=user,  # Use your custom user model
        defaults={
            "access_token": access_token,
            "refresh_token": refresh_token
        }
    )

    return {
        "access": access_token,
        "refresh": refresh_token
    }

