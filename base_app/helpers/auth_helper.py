from base_app.models import UserToken
from core.models import AdminToken
from supervisor.models import SupervisorToken
from django.utils import timezone
import jwt


def generate_custom_tokens(obj, role="user"):
    """
    Common Token Generator for User, Admin, Supervisor
    role = 'user' | 'admin' | 'supervisor'
    """

    # ✅ ID aur Name alag fields rakhte hain
    if role == "user":
        obj_id_field = "user_id"
        obj_name = obj.user_name
    elif role == "admin":
        obj_id_field = "admin_id"
        obj_name = obj.user_name
    elif role == "supervisor":
        obj_id_field = "supervisor_id"
        obj_name = obj.user_name
    else:
        raise ValueError("Invalid role. Use 'user', 'admin', or 'supervisor'.")

    # ✅ Access Token
    access_token_payload = {
        obj_id_field: obj.id,
        "user_name": obj_name,
        "iat": timezone.now().timestamp(),
        "token_type": "access"
    }
    access_token = jwt.encode(access_token_payload, "MagaIgnyte", algorithm="HS256")

    # ✅ Refresh Token
    refresh_token_payload = {
        obj_id_field: obj.id,
        "iat": timezone.now().timestamp(),
        "token_type": "refresh"
    }
    refresh_token = jwt.encode(refresh_token_payload, "MagaIgnyte", algorithm="HS256")

    # ✅ DB me save karo
    if role == "user":
        UserToken.objects.update_or_create(
            user=obj,
            defaults={"access_token": access_token, "refresh_token": refresh_token}
        )
    elif role == "admin":
        AdminToken.objects.update_or_create(
            admin=obj,
            defaults={"access_token": access_token, "refresh_token": refresh_token}
        )
    elif role == "supervisor":
        SupervisorToken.objects.update_or_create(
            supervisor=obj,
            defaults={"access_token": access_token, "refresh_token": refresh_token}
        )

    return {
        "access": access_token,
        "refresh": refresh_token
    }
