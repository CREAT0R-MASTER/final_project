import time
import uuid
from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view 
from rest_framework.response import Response
from rest_framework import status
from django.apps import apps

from ms_base_frame import settings
from .models import *
from base_app.serializers import *
from base_app.helpers.utility import app_name, get_serializer_class, get_filtered_queryset, CustomPageNumberPagination
from base_app.helpers.auth_helper import generate_custom_tokens
from django.contrib.auth.hashers import check_password
from django.core.mail import send_mail

from supervisor.models import SupervisorToken  
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.decorators import parser_classes



# -------- Supervisor Login API --------
@api_view(['POST'])
def supervisor_login(request):
    print("Supervisor Login API called")
    try:
        print("request data==> ", request.data)
        email = request.data.get("user_email")
        password = request.data.get("password")

        if not email or not password:
            return Response({"status": False, "message": "Email and password required"}, 
                          status=status.HTTP_400_BAD_REQUEST)

        supervisor = SupervisorProfile.objects.filter(user_email=email).first()
        print("supervisor found==> ", supervisor)
        
        if not supervisor:
            return Response({"status": False, "message": "Invalid credentials"}, 
                          status=status.HTTP_401_UNAUTHORIZED)

        # ✅✅✅ USE check_password FOR HASHED PASSWORDS
        print("supervisor password in DB:", supervisor.password[:50] + "..." if supervisor.password else "None")
        print("input password:", password)
        
        if not check_password(password, supervisor.password):
            return Response({"status": False, "message": "Invalid credentials"}, 
                          status=status.HTTP_401_UNAUTHORIZED)

        print("✅ Password matched!")
        
        # Delete existing tokens
        from supervisor.models import SupervisorToken
        SupervisorToken.objects.filter(supervisor=supervisor).delete()
        
        # Generate new tokens
        tokens = generate_custom_tokens(supervisor, role="supervisor")
        
        # Save token to database
        SupervisorToken.objects.create(
            supervisor=supervisor,
            access_token=tokens['access'],
            refresh_token=tokens['refresh']
        )
        
        serializer = SupervisorSerializer(supervisor)

        return Response({
            "status": True,
            "message": "Login successful",
            "access_token": tokens['access'],
            "refresh_token": tokens['refresh'],
            "supervisorData": serializer.data
        }, status=status.HTTP_200_OK)

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        print(f"🔍 Full traceback: {traceback.format_exc()}")
        return Response({"status": False, "message": str(e)}, 
                      status=status.HTTP_500_INTERNAL_SERVER_ERROR)    
        
# supervisor/views.py



@api_view(['GET'])
def assigned_complaints(request):
    """
    Complaints assigned to the logged-in supervisor.
    - Only show complaints assigned to this supervisor
    - Date descending
    - Status filter
    - Pagination
    """
    try:
        # ---------- Authenticate Supervisor ----------
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return Response({'status': False, 'message': 'Authentication required'}, status=401)

        supervisor_token = SupervisorToken.objects.filter(access_token=auth_header).first()
        if not supervisor_token:
            return Response({'status': False, 'message': 'Invalid token'}, status=401)

        supervisor = supervisor_token.supervisor  # 👈 supervisor profile milega

        # ---------- Filters ----------
        status_filter = request.GET.get('status', None)
        page = int(request.GET.get('page', 1))
        limit = int(request.GET.get('limit', 10))
        offset = (page - 1) * limit

        # ---------- Query ----------
        complaints = Complaint.objects.filter(
            assigned_supervisor=supervisor
        ).order_by('-created_datetime')

        if status_filter:
            complaints = complaints.filter(status=status_filter)

        total = complaints.count()
        complaints = complaints[offset:offset + limit]

        # ---------- Response Data ----------
        data = []
        for c in complaints:
            data.append({
                "complaint_id": c.complaint_id,
                "complaint_code": c.complaint_code,
                "complaint_category": getattr(c.complaint_category, "name", None),
                "complaint_subcategory": getattr(c.complaint_subcategory, "name", None),
                "zone": getattr(c.zone, "name", None),
                "ward": getattr(c.ward, "name", None),
                "description": c.description,
                "status": c.status,
                "created_datetime": c.created_datetime,
                "updated_datetime": getattr(c, 'updated_datetime', None),
                "created_by_name": f"{c.first_name} {c.last_name}" if hasattr(c, 'first_name') else None,
                "complaint_image": request.build_absolute_uri(c.complaint_image.url) if c.complaint_image else None
            })

        return Response({
            "status": True,
            "total_complaints": total,
            "page": page,
            "limit": limit,
            "data": data
        }, status=200)

    except Exception as e:
        return Response({"status": False, "message": str(e)}, status=500)
    
@api_view(['POST'])
@parser_classes([MultiPartParser, FormParser])
def resolve_complaint(request):
    """
    Supervisor resolves a complaint:
    - Can update status: pending, in progress, resolved
    - Can upload resolved image
    - Stores resolved_by & resolved_datetime
    - Sends email to user & admin when resolved
    """
    try:
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return Response({'status': False, 'message': 'Authentication required'}, status=401)

        supervisor_token = SupervisorToken.objects.filter(access_token=auth_header).first()
        if not supervisor_token:
            return Response({'status': False, 'message': 'Invalid token'}, status=401)

        supervisor = supervisor_token.supervisor

        complaint_id = request.data.get('complaint_id')
        if not complaint_id:
            return Response({'status': False, 'message': 'complaint_id is required'}, status=400)

        complaint = Complaint.objects.filter(complaint_id=complaint_id, assigned_supervisor=supervisor).first()
        if not complaint:
            return Response({'status': False, 'message': 'Complaint not found or not assigned to you'}, status=404)

        # Update status
        status_update = request.data.get('status')
        allowed_status = ['pending', 'in progress', 'resolved']
        if status_update not in allowed_status:
            return Response({'status': False, 'message': f"Status must be one of {allowed_status}"}, status=400)

        complaint.status = status_update

        # Upload resolved image
        resolved_image = request.FILES.get('resolved_image')
        if resolved_image:
            complaint.resolved_image = resolved_image

        # Set resolved_by & resolved_datetime if status is resolved
        if status_update == 'resolved':
            complaint.resolved_by = supervisor
            complaint.resolved_datetime = timezone.now()

        complaint.save()

        # Send emails if resolved
        if status_update == 'resolved':
            user_email = complaint.email
            admin_email = settings.ADMIN_EMAIL

            subject = f"Your complaint {complaint.complaint_code} is resolved"
            message = f"Hello {complaint.first_name},\n\nYour complaint has been resolved by the supervisor.\nStatus: {complaint.status}\nThank you."
            send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user_email])

            admin_message = f"Complaint {complaint.complaint_code} resolved by supervisor {supervisor.user_email}."
            send_mail(f"Complaint Resolved: {complaint.complaint_code}", admin_message, settings.DEFAULT_FROM_EMAIL, [admin_email])

        return Response({
            'status': True,
            'message': 'Complaint updated successfully',
            'complaint_id': complaint.complaint_id,
            'new_status': complaint.status,
            'resolved_image_url': request.build_absolute_uri(complaint.resolved_image.url) if resolved_image else None,
            'resolved_by': supervisor.user_email if status_update=='resolved' else None,
            'resolved_datetime': complaint.resolved_datetime if status_update=='resolved' else None
        }, status=200)

    except Exception as e:
        return Response({'status': False, 'message': str(e)}, status=500)

    
@api_view(['POST'])
def supervisor_logout(request):
    try:
        print("🔄 Supervisor Logout API called")
        
        # Direct Authorization header without "Bearer" prefix
        auth_header = request.headers.get("Authorization")
        print(f"🔑 Raw Authorization header: {auth_header}")
        
        if not auth_header:
            return Response(
                {"status": False, "message": "Authorization header required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Use token directly without "Bearer " removal
        access_token = auth_header.strip()
        print(f"🔑 Using token: {access_token}")

        # Token validation and deletion
        supervisor_token = SupervisorToken.objects.filter(access_token=access_token).first()

        if supervisor_token:
            supervisor_email = supervisor_token.supervisor.user_email
            supervisor_token.delete()
            print(f"✅ Logout successful for: {supervisor_email}")
            
            return Response(
                {"status": True, "message": "Logout successful"},
                status=status.HTTP_200_OK
            )

        print("❌ Invalid token provided")
        return Response(
            {"status": False, "message": "Invalid token"},
            status=status.HTTP_401_UNAUTHORIZED
        )

    except Exception as e:
        print(f"❌ Logout Error: {str(e)}")
        import traceback
        print(f"🔍 Full traceback: {traceback.format_exc()}")
        
        return Response(
            {"status": False, "message": "Internal server error"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )