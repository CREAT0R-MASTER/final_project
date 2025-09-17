import secrets
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.core.mail import send_mail
from django.conf import settings
from .models import Business
from .serializers import BusinessSerializer

from .models import SuperAdminToken

@api_view(['POST'])
def register_business(request):
    serializer = BusinessSerializer(data=request.data)
    if serializer.is_valid():
        business = serializer.save()

        # ✅ Notify superadmin
        try:
            send_mail(
                subject="New Business Registration Request",
                message=(
                    f"Business '{business.name}' was registered by {business.owner_name}.\n"
                    f"Email: {business.email}\n\nPlease login to Django Admin to approve."
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[settings.SUPERADMIN_EMAIL],
                fail_silently=True,
            )
        except Exception as e:
            print("Email send failed:", e)

        return Response({
            "status": True,
            "message": "Business registered successfully. Awaiting superadmin approval."
        }, status=status.HTTP_201_CREATED)

    return Response({
        "status": False,
        "errors": serializer.errors
    }, status=status.HTTP_400_BAD_REQUEST)


#Admin panel code

@api_view(['POST'])
def superadmin_login(request):
    email = request.data.get('email')
    password = request.data.get('password')

    if email == settings.SUPERADMIN_EMAIL and password == settings.SUPERADMIN_PASSWORD:
        # Delete old token if exists
        SuperAdminToken.objects.all().delete()
        
        # Generate new token
        token = "superadmin_" + secrets.token_urlsafe(16)
        SuperAdminToken.objects.create(token=token)

        return Response({'status': True, 'message': 'Login successful', 'token': token}, status=status.HTTP_200_OK)
    
    return Response({'status': False, 'message': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)


# ------------------- Logout -------------------
@api_view(['POST'])
def superadmin_logout(request):
    # Token body or header se read karo
    token = request.data.get('token') or request.headers.get('Authorization')

    if not token:
        return Response({'error': 'Token missing'}, status=status.HTTP_400_BAD_REQUEST)

    deleted, _ = SuperAdminToken.objects.filter(token=token).delete()
    if deleted:
        return Response({'status': True, 'message': 'Logout successful'}, status=status.HTTP_200_OK)
    else:
        return Response({'error': 'Invalid token'}, status=status.HTTP_401_UNAUTHORIZED)