# core/views.py

import random
import string
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.hashers import make_password, check_password

# Helpers & Models
from base_app.helpers.auth_helper import generate_custom_tokens
from base_app.models import SupervisorProfile, ComplaintCategory, ComplaintSubCategory, Complaint, Zone, Ward
from .models import AdminToken, AdminUser

# Serializers
from core.serializers import AdminUserSerializer, BusinessSerializer
from base_app.serializers import ComplaintCategorySerializer, ComplaintSubCategorySerializer, ComplaintSerializers, SupervisorSerializer, WardSerializer, ZoneSerializer

# ------------------ Helper Function ------------------
def authenticate_admin(request):
    """
    Validate admin token from headers.
    Returns (admin, None) if valid, else (None, Response).
    """
    token = request.headers.get('Authorization')
    if not token:
        return None, Response({"status": False, "message": "Token required"}, status=401)

    admin_token = AdminToken.objects.filter(access_token=token).first()
    if not admin_token:
        return None, Response({"status": False, "message": "Unauthorized - Invalid Token"}, status=401)

    return admin_token.admin, None


# ------------------ Business Registration ------------------
@api_view(['POST'])
def register_business(request):
    serializer = BusinessSerializer(data=request.data)
    if serializer.is_valid():
        business = serializer.save()

        # Send email to superadmin
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

        return Response(
            {"status": True, "message": "Business registered successfully. Awaiting superadmin approval."},
            status=201
        )
    return Response({"status": False, "errors": serializer.errors}, status=400)


# ------------------ Admin Signup ------------------
ADMIN_SECRET_KEY = "Nitesh@Admin2025"

@api_view(['POST'])
def admin_signup(request):
    try:
        # Extract fields
        user_name = request.data.get('user_name')
        user_email = request.data.get('user_email')
        contact_number = request.data.get('contact_number')
        password = request.data.get('password')
        confirm_password = request.data.get('confirm_password')
        secret_key = request.data.get('secret_key')

        # Validate required fields
        for field in ['user_name', 'user_email', 'contact_number', 'password', 'confirm_password', 'secret_key']:
            if not request.data.get(field):
                return Response({'status': False, 'message': f'{field.replace("_", " ").title()} is required'}, status=400)

        # Validate secret key
        if secret_key != ADMIN_SECRET_KEY:
            return Response({'status': False, 'message': 'Invalid secret key'}, status=403)

        # Validate passwords
        if password != confirm_password:
            return Response({'status': False, 'message': 'Passwords do not match'}, status=400)

        # Check for existing admin
        if AdminUser.objects.filter(user_email=user_email).exists():
            return Response({'status': False, 'message': 'Admin already exists'}, status=400)

        # Create new admin
        AdminUser.objects.create(
            user_name=user_name,
            user_email=user_email,
            contact_number=contact_number,
            password=make_password(password),
            user_type="ADMIN"
        )

        return Response({'status': True, 'message': 'Admin signup successful'}, status=201)

    except Exception as e:
        return Response({'status': False, 'message': 'Internal Server Error', 'error': str(e)}, status=500)


# ------------------ Admin Login ------------------
@api_view(['POST'])
def admin_login(request):
    try:
        user_email = request.data.get('user_email')
        password = request.data.get('password')

        if not user_email or not password:
            return Response({'status': False, 'message': 'Email and password are required'}, status=400)

        admin = AdminUser.objects.filter(user_email=user_email).first()
        if not admin or not check_password(password, admin.password):
            return Response({'status': False, 'message': 'Invalid credentials'}, status=401)

        tokens = generate_custom_tokens(admin, role="admin")
        admin_serializer = AdminUserSerializer(admin)

        return Response({
            'status': True,
            'message': 'Login successful',
            'access_token': tokens['access'],
            'refresh_token': tokens['refresh'],
            'adminData': admin_serializer.data
        }, status=200) 

    except Exception as e:
        return Response({'status': False, 'message': str(e)}, status=500)


# ------------------ Complaint Category API ------------------
@api_view(['GET', 'POST', 'PUT', 'DELETE'])
def complaint_category_api(request, pk=None):
    admin, error = authenticate_admin(request)
    if error:
        return error

    if request.method == 'GET':
        if pk:
            category = ComplaintCategory.objects.filter(id=pk).first()
            if not category:
                return Response({'status': False, 'message': 'Category not found'}, status=404)
            serializer = ComplaintCategorySerializer(category)
            return Response({'status': True, 'data': serializer.data})
        categories = ComplaintCategory.objects.all()
        serializer = ComplaintCategorySerializer(categories, many=True)
        return Response({'status': True, 'data': serializer.data})

    if request.method == 'POST':
        serializer = ComplaintCategorySerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({'status': True, 'message': 'Category created', 'data': serializer.data})
        return Response({'status': False, 'message': serializer.errors}, status=400)

    if request.method == 'PUT':
        if not pk:
            return Response({'status': False, 'message': 'ID required'}, status=400)
        category = ComplaintCategory.objects.filter(id=pk).first()
        if not category:
            return Response({'status': False, 'message': 'Category not found'}, status=404)
        serializer = ComplaintCategorySerializer(category, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({'status': True, 'message': 'Category updated', 'data': serializer.data})
        return Response({'status': False, 'message': serializer.errors}, status=400)

    if request.method == 'DELETE':
        if not pk:
            return Response({'status': False, 'message': 'ID required'}, status=400)
        category = ComplaintCategory.objects.filter(id=pk).first()
        if not category:
            return Response({'status': False, 'message': 'Category not found'}, status=404)
        category.delete()
        return Response({'status': True, 'message': 'Category deleted'})


# ------------------ Complaint SubCategory API ------------------
@api_view(['GET', 'POST', 'PUT', 'DELETE'])
def complaint_subcategory_api(request, pk=None):
    admin, error = authenticate_admin(request)
    if error:
        return error

    if request.method == 'GET':
        if pk:
            subcategory = ComplaintSubCategory.objects.filter(id=pk).first()
            if not subcategory:
                return Response({'status': False, 'message': 'SubCategory not found'}, status=404)
            serializer = ComplaintSubCategorySerializer(subcategory)
            return Response({'status': True, 'data': serializer.data})
        subcategories = ComplaintSubCategory.objects.all()
        serializer = ComplaintSubCategorySerializer(subcategories, many=True)
        return Response({'status': True, 'data': serializer.data})

    if request.method == 'POST':
        serializer = ComplaintSubCategorySerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({'status': True, 'message': 'SubCategory created', 'data': serializer.data})
        return Response({'status': False, 'message': serializer.errors}, status=400)

    if request.method == 'PUT':
        if not pk:
            return Response({'status': False, 'message': 'ID required'}, status=400)
        subcategory = ComplaintSubCategory.objects.filter(id=pk).first()
        if not subcategory:
            return Response({'status': False, 'message': 'SubCategory not found'}, status=404)
        serializer = ComplaintSubCategorySerializer(subcategory, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({'status': True, 'message': 'SubCategory updated', 'data': serializer.data})
        return Response({'status': False, 'message': serializer.errors}, status=400)

    if request.method == 'DELETE':
        if not pk:
            return Response({'status': False, 'message': 'ID required'}, status=400)
        subcategory = ComplaintSubCategory.objects.filter(id=pk).first()
        if not subcategory:
            return Response({'status': False, 'message': 'SubCategory not found'}, status=404)
        subcategory.delete()
        return Response({'status': True, 'message': 'SubCategory deleted'})
    
    
#-------------------zone api------------------------------------

@api_view(['GET', 'POST', 'PUT', 'DELETE'])
def zone_api(request, pk=None):
    admin, error = authenticate_admin(request)
    if error:
        return error

    if request.method == 'GET':
        if pk:
            zone = Zone.objects.filter(id=pk).first()
            if not zone:
                return Response({'status': False, 'message': 'Zone not found'}, status=404)
            serializer = ZoneSerializer(zone)
            return Response({'status': True, 'data': serializer.data})
        zones = Zone.objects.all()
        serializer = ZoneSerializer(zones, many=True)
        return Response({'status': True, 'data': serializer.data})

    if request.method == 'POST':
        serializer = ZoneSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({'status': True, 'message': 'Zone created', 'data': serializer.data})
        return Response({'status': False, 'message': serializer.errors}, status=400)

    if request.method == 'PUT':
        if not pk:
            return Response({'status': False, 'message': 'ID required'}, status=400)
        zone = Zone.objects.filter(id=pk).first()
        if not zone:
            return Response({'status': False, 'message': 'Zone not found'}, status=404)
        serializer = ZoneSerializer(zone, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({'status': True, 'message': 'Zone updated', 'data': serializer.data})
        return Response({'status': False, 'message': serializer.errors}, status=400)

    if request.method == 'DELETE':
        if not pk:
            return Response({'status': False, 'message': 'ID required'}, status=400)
        zone = Zone.objects.filter(id=pk).first()
        if not zone:
            return Response({'status': False, 'message': 'Zone not found'}, status=404)
        zone.delete()
        return Response({'status': True, 'message': 'Zone deleted'})


# ------------------ Ward API ------------------
@api_view(['GET', 'POST', 'PUT', 'DELETE'])
def ward_api(request, pk=None):
    admin, error = authenticate_admin(request)
    if error:
        return error

    if request.method == 'GET':
        if pk:
            ward = Ward.objects.filter(id=pk).first()
            if not ward:
                return Response({'status': False, 'message': 'Ward not found'}, status=404)
            serializer = WardSerializer(ward)
            return Response({'status': True, 'data': serializer.data})
        wards = Ward.objects.all()
        serializer = WardSerializer(wards, many=True)
        return Response({'status': True, 'data': serializer.data})

    if request.method == 'POST':
        serializer = WardSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({'status': True, 'message': 'Ward created', 'data': serializer.data})
        return Response({'status': False, 'message': serializer.errors}, status=400)

    if request.method == 'PUT':
        if not pk:
            return Response({'status': False, 'message': 'ID required'}, status=400)
        ward = Ward.objects.filter(id=pk).first()
        if not ward:
            return Response({'status': False, 'message': 'Ward not found'}, status=404)
        serializer = WardSerializer(ward, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({'status': True, 'message': 'Ward updated', 'data': serializer.data})
        return Response({'status': False, 'message': serializer.errors}, status=400)

    if request.method == 'DELETE':
        if not pk:
            return Response({'status': False, 'message': 'ID required'}, status=400)
        ward = Ward.objects.filter(id=pk).first()
        if not ward:
            return Response({'status': False, 'message': 'Ward not found'}, status=404)
        ward.delete()
        return Response({'status': True, 'message': 'Ward deleted'})


@api_view(['GET', 'POST', 'PUT', 'DELETE'])
def complaint_management_api(request, pk=None):
    # ---------- Authenticate Admin ----------
    admin, error = authenticate_admin(request)
    if error:
        return error
    is_admin_request = admin is not None

    # ---------- GET ----------
    if request.method == 'GET':
        if pk:
            complaint = Complaint.objects.filter(pk=pk).first()
            if not complaint:
                return Response({'status': False, 'message': 'Complaint not found'}, status=404)
            # Admin can view all, user only their own complaints
            if not is_admin_request and complaint.created_by != admin:
                return Response({'status': False, 'message': 'Not authorized'}, status=403)
            serializer = ComplaintSerializers(complaint)
            return Response({'status': True, 'data': serializer.data})

        # List all complaints
        complaints = Complaint.objects.all().order_by('-created_datetime')
        serializer = ComplaintSerializers(complaints, many=True)
        return Response({'status': True, 'data': serializer.data})

    # ---------- POST (Create Complaint) ----------
    if request.method == 'POST':
        if not is_admin_request:
            return Response({'status': False, 'message': 'Unauthorized'}, status=401)
        data = request.data.copy()
        data['created_by'] = admin.id  # Auto assign admin as creator
        serializer = ComplaintSerializers(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response({'status': True, 'message': 'Complaint created', 'data': serializer.data})
        return Response({'status': False, 'message': serializer.errors}, status=400)

    # ---------- PUT (Update / Assign Supervisor) ----------
    if request.method == 'PUT':
        if not pk:
            return Response({'status': False, 'message': 'Complaint ID required'}, status=400)
        complaint = Complaint.objects.filter(pk=pk).first()
        if not complaint:
            return Response({'status': False, 'message': 'Complaint not found'}, status=404)
        if not is_admin_request:
            return Response({'status': False, 'message': 'Not authorized'}, status=403)

        # Assign supervisor logic (zone & ward match)
        supervisor_id = request.data.get('supervisor_id')
        if supervisor_id:
            supervisor = SupervisorProfile.objects.filter(
                pk=supervisor_id,
                zone=complaint.zone,
                ward=complaint.ward
            ).first()
            if not supervisor:
                return Response({'status': False, 'message': 'Invalid Supervisor ID for this Zone/Ward'}, status=400)
            complaint.assigned_supervisor = supervisor

        # Update other complaint fields if needed
        serializer = ComplaintSerializers(complaint, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({'status': True, 'message': 'Complaint updated', 'data': serializer.data})
        return Response({'status': False, 'message': serializer.errors}, status=400)

    # ---------- DELETE ----------
    if request.method == 'DELETE':
        if not pk:
            return Response({'status': False, 'message': 'Complaint ID required'}, status=400)
        complaint = Complaint.objects.filter(pk=pk).first()
        if not complaint:
            return Response({'status': False, 'message': 'Complaint not found'}, status=404)
        complaint.delete()
        return Response({'status': True, 'message': 'Complaint deleted'})



# ------------------- Supervisor API -------------------

@api_view(['GET', 'POST', 'PUT', 'DELETE'])
def supervisor_api(request, pk=None):
    # -------- Authenticate admin --------
    admin, error = authenticate_admin(request)
    if error:
        return error

    # -------- GET (single ya list) --------
    if request.method == 'GET':
        if pk:
            supervisor = SupervisorProfile.objects.filter(pk=pk, user_type="SUPERVISOR").first()
            if not supervisor:
                return Response({'status': False, 'message': 'Supervisor not found'}, status=404)
            serializer = SupervisorSerializer(supervisor)
            return Response({'status': True, 'data': serializer.data})

        supervisors = SupervisorProfile.objects.filter(user_type="SUPERVISOR")
        serializer = SupervisorSerializer(supervisors, many=True)
        return Response({'status': True, 'data': serializer.data})

    # -------- POST (add new supervisor) --------
    if request.method == 'POST':
        data = request.data.copy()
        data['created_by'] = admin.id  # Track which admin created

        # -------- Admin must provide password --------
        if 'password' not in data or not data['password']:
            return Response({'status': False, 'message': 'Password is required for supervisor'}, status=400)
        
        admin_password = data['password']  # Store plain password for email
        
        # ✅✅✅ HASH THE PASSWORD BEFORE SAVING
        data['password'] = make_password(data['password'])
        print(f"🔐 Password hashed for: {data.get('user_email')}")

        serializer = SupervisorSerializer(data=data)
        if serializer.is_valid():
            supervisor = serializer.save()  # Save supervisor in DB with hashed password

            # -------- Send email to supervisor with admin-provided password --------
            subject = "Your Supervisor Account Created"
            message = f"""
Hello {supervisor.user_name},

Your account has been created by admin.
Email: {supervisor.user_email}
Password: {admin_password}  # Send plain password in email

Please login and change your password after first login.
"""
            from_email = None  # Use default EMAIL_HOST settings
            recipient_list = [supervisor.user_email]
            send_mail(subject, message, from_email, recipient_list, fail_silently=False)

            return Response({'status': True, 'message': 'Supervisor created successfully and email sent', 'data': serializer.data})

        return Response({'status': False, 'message': serializer.errors}, status=400)

    # -------- PUT (update supervisor) --------
    if request.method == 'PUT':
        if not pk:
            return Response({'status': False, 'message': 'Supervisor ID required'}, status=400)

        supervisor = SupervisorProfile.objects.filter(pk=pk, user_type="SUPERVISOR").first()
        if not supervisor:
            return Response({'status': False, 'message': 'Supervisor not found'}, status=404)

        data = request.data.copy()
        data['updated_by'] = admin.id

        # ✅✅✅ If password is being updated, hash it
        if 'password' in data and data['password']:
            print(f"🔐 Updating password for supervisor ID: {pk}")
            data['password'] = make_password(data['password'])

        serializer = SupervisorSerializer(supervisor, data=data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({'status': True, 'message': 'Supervisor updated successfully', 'data': serializer.data})
        return Response({'status': False, 'message': serializer.errors}, status=400)

    # -------- DELETE (remove supervisor) --------
    if request.method == 'DELETE':
        if not pk:
            return Response({'status': False, 'message': 'Supervisor ID required'}, status=400)

        supervisor = SupervisorProfile.objects.filter(pk=pk, user_type="SUPERVISOR").first()
        if not supervisor:
            return Response({'status': False, 'message': 'Supervisor not found'}, status=404)

        supervisor.delete()
        return Response({'status': True, 'message': 'Supervisor deleted successfully'})
    

#------------------ Dashboard Statistics API ------------------
@api_view(['GET'])
def dashboard_statistics(request):
    # Authenticate admin using helper
    admin, error = authenticate_admin(request)
    if error:
        return error  # Agar token invalid ya missing ho to yahi response milega

    try:
        # Complaint statistics
        total_complaints = Complaint.objects.count()
        pending_complaints = Complaint.objects.filter(status='pending').count()
        in_progress_complaints = Complaint.objects.filter(status='in_progress').count()
        resolved_complaints = Complaint.objects.filter(status='resolved').count()
        register_complaints = total_complaints  # Total registered complaints

        # Category statistics
        total_categories = ComplaintCategory.objects.count()
        total_subcategories = ComplaintSubCategory.objects.count()

        # Graph data for overall complaints including registered complaints
        overall_complaints_graph = {
            "Registered": register_complaints,
            "Pending": pending_complaints,
            "In Progress": in_progress_complaints,
            "Resolved": resolved_complaints
        }

        # Graph data for progress per category including total complaints per category
        overall_progress_graph = [
            {
                "category": c.name,
                "Total": Complaint.objects.filter(complaint_category=c).count(),
                "Pending": Complaint.objects.filter(complaint_category=c, status='pending').count(),
                "In Progress": Complaint.objects.filter(complaint_category=c, status='in_progress').count(),
                "Resolved": Complaint.objects.filter(complaint_category=c, status='resolved').count()
            }
            for c in ComplaintCategory.objects.all()
        ]

        # Complaints grouped by category
        complaints_by_category = [
            {
                'category': c.name,
                'count': Complaint.objects.filter(complaint_category=c).count()
            }
            for c in ComplaintCategory.objects.all()
        ]

        # Complaints grouped by subcategory
        complaints_by_subcategory = [
            {
                'subcategory': sc.name,
                'count': Complaint.objects.filter(complaint_subcategory=sc).count()
            }
            for sc in ComplaintSubCategory.objects.all()
        ]

        # Recent complaints
        recent_complaints = Complaint.objects.all().order_by('-created_datetime')[:10]
        recent_complaints_data = ComplaintSerializers(recent_complaints, many=True).data

        return Response({
            'status': True,
            'data': {
                'total_complaints': total_complaints,
                'pending_complaints': pending_complaints,
                'in_progress_complaints': in_progress_complaints,
                'resolved_complaints': resolved_complaints,
                'register_complaints': register_complaints,
                'total_categories': total_categories,
                'total_subcategories': total_subcategories,
                'overall_complaints_graph': overall_complaints_graph,
                'overall_progress_graph': overall_progress_graph,
                'complaints_by_category': complaints_by_category,
                'complaints_by_subcategory': complaints_by_subcategory,
                'recent_complaints': recent_complaints_data
            }
        }, status=200)

    except Exception as e:
        return Response({'status': False, 'message': str(e)}, status=500)


# ------------------ Admin Logout ------------------
@api_view(['POST'])
def admin_logout(request):
    try:
        access_token = request.data.get("token")
        if not access_token:
            return Response({"status": False, "message": "Token required"}, status=400)

        admin_token = AdminToken.objects.filter(access_token=access_token).first()
        if admin_token:
            admin_token.delete()
            return Response({"status": True, "message": "Logout successful"}, status=200)

        return Response({"status": False, "message": "Invalid token"}, status=401)

    except Exception as e:
        return Response({"status": False, "message": str(e)}, status=500)
