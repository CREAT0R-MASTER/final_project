import time
from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view 
from rest_framework.response import Response
from rest_framework import status
from django.apps import apps
from .models import *
from .serializers import *
from .helpers.utility import app_name, get_serializer_class, get_filtered_queryset, CustomPageNumberPagination
from .helpers.auth_helper import generate_custom_tokens
from django.contrib.auth.hashers import make_password, check_password

from base_app.models import ComplaintCategory, ComplaintSubCategory, Zone, Ward
from .models import UserToken, Complaint
from .serializers import ComplaintSerializers
from math import radians, cos, sin, asin, sqrt
from django.core.mail import send_mail
from django.conf import settings
import random


@api_view(['GET', 'POST', 'PUT', 'DELETE'])
def manage_data(request, model_name, field=None, value=None, item_id=None):            
            
    try:
        model_class = apps.get_model(app_name, model_name)
    except LookupError:
        return Response({'error': f'Model "{model_name}" not found'}, status=status.HTTP_404_NOT_FOUND)

    try:
        serializer_class = get_serializer_class(model_name)
    except (ImportError, AttributeError) as e:
        return Response({'error': str(e)}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        try:
            queryset = get_filtered_queryset(model_class, field, value, request.query_params).order_by('id')

            paginator = CustomPageNumberPagination()
            paginated_qs = paginator.paginate_queryset(queryset, request)
            serializer = serializer_class(paginated_qs, many=True)

            return paginator.get_paginated_response(serializer.data)
        except Exception as e:
            return Response({'status': False, 'message': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    

    elif request.method == 'POST':
        try:
            request_data = request.data.copy() if hasattr(request.data, 'copy') else request.data
            serializer = serializer_class(data=request_data)
            if serializer.is_valid():
                serializer.save() 
                return Response({'status': True, 'data': serializer.data}, status=status.HTTP_201_CREATED)
            else:
                print(serializer.errors)
                return Response({"status": False, "message": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({'status': False, 'message': 'Internal Server Error', 'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


    elif request.method == 'DELETE':
        try:
            queryset = None

            if item_id:
                item = get_object_or_404(model_class, pk=item_id)
                item.delete()
                return Response({'status': True, 'message': 'Item deleted successfully'})

            elif field and value:
                queryset = model_class.objects.filter(**{field: value})
            elif request.query_params:
                filters = request.query_params.dict()
                queryset = model_class.objects.filter(**filters)

            if not queryset or not queryset.exists():
                return Response({'status': False, 'message': 'No matching items found'}, status=status.HTTP_404_NOT_FOUND)
            
            delete_multiple = False
            try:
                delete_multiple = request.data.get('delete_multiple', False)
            except Exception:
                pass

            if delete_multiple:
                count, _ = queryset.delete()
                return Response({'status': True, 'message': f'{count} items deleted successfully'}, status=status.HTTP_200_OK)
            elif queryset.count() > 1:
                return Response({'status': False, 'message': 'Multiple items matched. Set delete_multiple=true to confirm bulk delete.'}, status=status.HTTP_400_BAD_REQUEST)
            else:
                queryset.first().delete()
                return Response({'status': True, 'message': 'Item deleted successfully'})

        except Exception as e:
            return Response({'status': False, 'message': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


    elif request.method == 'PUT':
        try:
            request_data = request.data.copy() if hasattr(request.data, 'copy') else request.data
            update_multiple = request_data.pop('update_multiple', False)

            queryset = None

            if item_id:
                queryset = model_class.objects.filter(pk=item_id)
            elif field and value:
                queryset = model_class.objects.filter(**{field: value})
            elif request.query_params:
                filters = request.query_params.dict()
                queryset = model_class.objects.filter(**filters)
            else:
                return Response({'status': False, 'message': 'Missing item_id or field/value pair or query filters'}, status=status.HTTP_400_BAD_REQUEST)

            if not queryset.exists():
                return Response({'status': False, 'message': 'No matching items found'}, status=status.HTTP_404_NOT_FOUND)

            if update_multiple:
                updated_count = 0
                for instance in queryset:
                    serializer = serializer_class(instance, data=request_data, partial=True)
                    if serializer.is_valid():
                        serializer.save()
                        updated_count += 1
                    else:
                        return Response({
                            'status': False,
                            'message': 'Validation failed on one or more records',
                            'errors': serializer.errors
                        }, status=status.HTTP_400_BAD_REQUEST)

                return Response({'status': True, 'message': f'{updated_count} items updated successfully'}, status=status.HTTP_200_OK)

            if queryset.count() > 1:
                return Response({
                    'status': False,
                    'message': 'Multiple items matched. Set "update_multiple": true to update all.'
                }, status=400)

            instance = queryset.first()
            serializer = serializer_class(instance, data=request_data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response({'status': True, 'message': 'Item updated successfully'}, status=status.HTTP_200_OK)
            else:
                return Response({'status': False, 'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({'status': False, 'message': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
def login(request):
    try:
        user_email = request.data.get('user_email')
        user_password = request.data.get('password')
        if not user_email or not user_password:
            return Response({'status': False, 'message': 'Email and password required'}, status=status.HTTP_400_BAD_REQUEST)

        userInstance = UserProfile.objects.filter(user_email=user_email).first()
        if userInstance and check_password(user_password, userInstance.password):
            UserToken.objects.filter(user=userInstance).delete()
            tokens = generate_custom_tokens(userInstance)


            userSerilizer = UserProfileSerializers(userInstance)

            return Response({'status': True, 'message': 'Login successful', 'token': tokens['access'], 'userData': userSerilizer.data}, status=status.HTTP_200_OK)
        else:
            return Response({'status': False, 'message': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)

    except Exception as e:
        return Response({'status': False, 'message': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
def signup(request):
    try:
        user_id = request.data.get('user_id')
        created_by = request.data.get('created_by')  # Changed from created_by_ID
        updated_by = request.data.get('updated_by')  # Changed from updated_by_ID
        created_datetime = request.data.get('created_datetime')
        updated_datetime = request.data.get('updated_datetime')
        user_name = request.data.get('user_name')
        business_name = request.data.get('business_name')
        user_email = request.data.get('user_email')
        contact_number = request.data.get('contact_number')
        password = request.data.get('password')
        confirm_password = request.data.get('confirm_password')
        address = request.data.get('address')
        city = request.data.get('city')
        state = request.data.get('state')

        # Required fields check
        required_fields = ['user_name', 'user_email', 'contact_number', 'password', 'confirm_password', 'address']
        for field in required_fields:
            if not request.data.get(field):
                return Response({'status': False, 'message': f'{field.replace("_", " ").title()} is required'}, 
                              status=status.HTTP_400_BAD_REQUEST)

        # Password confirmation check
        if password != confirm_password:
            return Response({'status': False, 'message': 'Passwords do not match'}, 
                          status=status.HTTP_400_BAD_REQUEST)

        if UserProfile.objects.filter(user_email=user_email).exists():
            return Response({'status': False, 'message': 'User already exists'}, status=status.HTTP_400_BAD_REQUEST)

        user = UserProfile.objects.create(
            user_id=user_id,
            user_name=user_name,
            user_type="CITIZEN",  # Default to citizen
            user_email=user_email,
            contact_number=contact_number,
            password=make_password(password),
            address=address,
            city=city,
            state=state,
            created_by=created_by,  # Changed from created_by_ID
            updated_by=updated_by,  # Changed from updated_by_ID
            created_datetime=created_datetime,
            updated_datetime=updated_datetime
        )

        return Response({'status': True, 'message': 'Signup successful'}, status=status.HTTP_201_CREATED)

    except Exception as e:
        return Response({'status': False, 'message': 'Internal Server Error', 'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    
    # User panel code

@api_view(['GET'])
def dropdown_values(request, dropdown_type):
    try:
        data = []

        # Complaint Category
        if dropdown_type == 'complaint_category':
            values = ComplaintCategory.objects.filter(is_active=True)
            data = [{'id': v.id, 'name': v.name} for v in values]

        # Complaint SubCategory (category_id required)
        elif dropdown_type == 'complaint_subcategory':
            category_id = request.query_params.get('category_id')
            if not category_id:
                return Response({'status': False, 'message': 'category_id is required for subcategories'}, status=400)
            values = ComplaintSubCategory.objects.filter(is_active=True, category_id=category_id)
            data = [{'id': v.id, 'name': v.name} for v in values]

        # Zone
        elif dropdown_type == 'zone':
            values = Zone.objects.filter(is_active=True)
            data = [{'id': v.id, 'name': v.name} for v in values]

        # Ward (zone_id required)
        elif dropdown_type == 'ward':
            zone_id = request.query_params.get('zone_id')
            if not zone_id:
                return Response({'status': False, 'message': 'zone_id is required for wards'}, status=400)
            values = Ward.objects.filter(is_active=True, zone_id=zone_id)
            data = [{'id': v.id, 'name': v.name} for v in values]

        else:
            return Response({'status': False, 'message': 'Invalid dropdown type'}, status=400)

        return Response({'status': True, 'data': data}, status=200)

    except Exception as e:
        return Response({'status': False, 'message': str(e)}, status=500)

@api_view(['POST'])
def create_complaint(request):
    try:
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return Response({'status': False, 'message': 'Authentication required'}, status=401)
        
        user_token = UserToken.objects.filter(access_token=auth_header).first()
        if not user_token:
            return Response({'status': False, 'message': 'Invalid token'}, status=401)
        
        user = user_token.user

        # Validate complaint category
        complaint_category_name = request.data.get('complaint_category')
        if not complaint_category_name:
            return Response({'status': False, 'message': 'Invalid complaint category'}, status=400)
        
        category_instance = ComplaintCategory.objects.filter(name=complaint_category_name, is_active=True).first()
        if not category_instance:
            return Response({'status': False, 'message': 'Invalid complaint category'}, status=400)

        # Validate complaint subcategory
        sub_category_name = request.data.get('complaint_subcategory')
        if not sub_category_name:
            return Response({'status': False, 'message': 'Complaint subcategory is required'}, status=400)
        sub_category_instance = ComplaintSubCategory.objects.filter(
            category=category_instance,
            name=sub_category_name,
            is_active=True
        ).first()
        if not sub_category_instance:
            return Response({'status': False, 'message': 'Invalid complaint sub-category'}, status=400)

        # Validate zone
        zone_name = request.data.get('zone')
        zone_instance = Zone.objects.filter(name=zone_name, is_active=True).first()
        if not zone_instance:
            return Response({'status': False, 'message': 'Invalid zone'}, status=400)
        
        # Validate ward based on selected zone
        ward_name = request.data.get('ward')
        ward_instance = Ward.objects.filter(name=ward_name, zone=zone_instance, is_active=True).first()
        if not ward_instance:
            return Response({'status': False, 'message': 'Invalid ward for selected zone'}, status=400)

        # ✅ Safe copy of request.data so we can modify (instead of direct modify)
        data = request.data.copy()

        # Pre-fill user info safely
        full_name = user.user_name.strip() if user.user_name else ''
        name_parts = full_name.split(' ')
        data['first_name'] = name_parts[0] if len(name_parts) > 0 else ''
        data['last_name'] = ' '.join(name_parts[1:]) if len(name_parts) > 1 else 'N/A' 
        data['mobile'] = user.contact_number or ''
        data['email'] = user.user_email or ''
        data['address1'] = user.address or ''
        data['area'] = user.city if user.city else 'N/A' 
        data['created_by'] = user.id

        # Handle image upload
        complaint_image = request.FILES.get('complaint_image')
        if not complaint_image:
            return Response({'status': False, 'message': 'Complaint image is required'}, status=400)
        data['complaint_image'] = complaint_image

        # Save complaint
        serializer = ComplaintSerializers(data=data)
        if serializer.is_valid():
            complaint = serializer.save(status='registered')

            # ✅ safer way: prepare response separately
            response_data = serializer.data
            response_data['complaint_subcategory'] = sub_category_instance.name

            return Response({
                'status': True,
                'message': 'Complaint registered successfully',
                'complaint_code': complaint.complaint_code,
                'data': response_data
            }, status=201)
        else:
            return Response({
                'status': False,
                'message': 'Validation failed',
                'errors': serializer.errors
            }, status=400)

    except Exception as e:
        return Response({'status': False, 'message': str(e)}, status=500)
    
    
@api_view(['GET'])
def complaint_detail(request, complaint_id):
    try:
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return Response({'status': False, 'message': 'Authentication required'}, status=401)

        user_token = UserToken.objects.filter(access_token=auth_header).first()
        if not user_token:
            return Response({'status': False, 'message': 'Invalid token'}, status=401)

        user = user_token.user

        # Complaint fetch
        complaint = Complaint.objects.filter(
            complaint_id=complaint_id,
            created_by=user
        ).first()

        if not complaint:
            return Response({'status': False, 'message': 'Complaint not found'}, status=404)

        # Supervisor info (optional)
        supervisor_data = None
        supervisor_assign_status = "pending"
        if hasattr(complaint, 'supervisor') and complaint.supervisor:
            supervisor_data = {
                "supervisor_id": complaint.supervisor.id,
                "name": complaint.supervisor.name,
                "email": complaint.supervisor.email,
                "mobile": complaint.supervisor.mobile
            }
            supervisor_assign_status = "assigned"

        # Complaint data
        data = {
            "complaint_id": complaint.complaint_id,
            "complaint_code": complaint.complaint_code,
            "complaint_category": complaint.complaint_category,
            "complaint_subcategory": getattr(complaint, 'complaint_subcategory', None),
            "zone": complaint.zone,
            "ward": complaint.ward,
            "description": complaint.description,
            "status": complaint.status,
            "created_datetime": complaint.created_datetime,
            "updated_datetime": getattr(complaint, 'updated_datetime', None),
            "created_by_name": f"{complaint.first_name} {complaint.last_name}",
            "complaint_image": request.build_absolute_uri(complaint.complaint_image.url) if complaint.complaint_image else None,
            "supervisor_assign_status": supervisor_assign_status,
            "supervisor": supervisor_data
        }

        return Response({"status": True, "data": data}, status=200)

    except Exception as e:
        return Response({"status": False, "message": str(e)}, status=500)
        
        
@api_view(['GET'])
def complaint_status(request, complaint_code):
    try:
        complaint = get_object_or_404(Complaint, complaint_code=complaint_code)
        serializer = ComplaintSerializers(complaint)
        return Response({'status': True, 'data': serializer.data})
    except Complaint.DoesNotExist:
        return Response({'status': False, 'message': 'Complaint not found'}, status=404)
    except Exception as e:
        return Response({'status': False, 'message': str(e)}, status=500)
    
    
@api_view(['GET'])
def recent_complaints(request):
    """
    Recent complaints for the logged-in user:
    - Only show complaints created by this user
    - Date descending
    - Status filter
    - Pagination
    - Includes updates on complaints
    """
    try:
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return Response({'status': False, 'message': 'Authentication required'}, status=401)

        user_token = UserToken.objects.filter(access_token=auth_header).first()
        if not user_token:
            return Response({'status': False, 'message': 'Invalid token'}, status=401)

        user = user_token.user

        status_filter = request.GET.get('status', None)
        page = int(request.GET.get('page', 1))
        limit = int(request.GET.get('limit', 10))
        offset = (page - 1) * limit

        # Filter complaints by the logged-in user
        complaints = Complaint.objects.filter(created_by=user).order_by('-created_datetime')

        if status_filter:
            complaints = complaints.filter(status=status_filter)

        total = complaints.count()
        complaints = complaints[offset:offset + limit]

        data = []
        for c in complaints:
            data.append({
                "complaint_id": c.complaint_id,
                "complaint_code": c.complaint_code,
                "complaint_category": c.complaint_category,
                "complaint_subcategory": getattr(c, 'complaint_subcategory', None),
                "zone": c.zone,
                "ward": c.ward,
                "description": c.description,
                "status": c.status,
                "created_datetime": c.created_datetime,
                "updated_datetime": getattr(c, 'updated_datetime', None),  # agar update field hai
                "created_by_name": f"{c.first_name} {c.last_name}",
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

    
@api_view(['GET'])
def get_complaint_by_number(request, complaint_code):
    """
    Citizen can view their complaint details using complaint number
    """
    try:
        complaint = get_object_or_404(Complaint, complaint_code=complaint_code)
        
        # Sirf citizen ke liye relevant fields
        data = {
            "complaint_id": complaint.complaint_id,
            "complaint_code": complaint.complaint_code,
            "complaint_category": complaint.complaint_category,
            "zone": complaint.zone,
            "ward": complaint.ward,
            "description": complaint.description,
            "status": complaint.status,
            "created_datetime": complaint.created_datetime,
            "created_by_name": f"{complaint.first_name} {complaint.last_name}"
        }

        return Response({"status": True, "data": data}, status=200)

    except Complaint.DoesNotExist:
        return Response({"status": False, "message": "Complaint not found"}, status=404)
    except Exception as e:
        return Response({"status": False, "message": str(e)}, status=500)
    

def haversine(lon1, lat1, lon2, lat2):
    """
    Calculate the great circle distance in km between two points 
    on the earth (specified in decimal degrees)
    """
    # convert decimal degrees to radians
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    
    # haversine formula
    dlon = lon2 - lon1 
    dlat = lat2 - lat1 
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a)) 
    r = 6371  # Radius of earth in km
    return c * r

@api_view(['GET'])
def nearby_complaints(request):
    try:
        lat = request.GET.get('latitude')
        lon = request.GET.get('longitude')
        radius = float(request.GET.get('radius', 5))  # Default 5 km

        if not lat or not lon:
            return Response({"status": False, "message": "latitude and longitude are required"}, status=400)

        lat = float(lat)
        lon = float(lon)

        complaints = Complaint.objects.all()
        nearby = []

        for c in complaints:
            if c.latitude is not None and c.longitude is not None:
                distance = haversine(lon, lat, c.longitude, c.latitude)
                if distance <= radius:
                    nearby.append({
                        "complaint_id": c.complaint_id,
                        "complaint_code": c.complaint_code,
                        "complaint_category": c.complaint_category,
                        "zone": c.zone,
                        "ward": c.ward,
                        "description": c.description,
                        "status": c.status,
                        "created_datetime": c.created_datetime,
                        "distance_km": round(distance, 2),
                        "created_by_name": f"{c.first_name} {c.last_name}",
                        "complaint_image": request.build_absolute_uri(c.complaint_image.url) if c.complaint_image else None

                    })

        # Sort by recent datetime
        nearby.sort(key=lambda x: x['created_datetime'], reverse=True)

        return Response({"status": True, "total": len(nearby), "data": nearby}, status=200)

    except Exception as e:
        return Response({"status": False, "message": str(e)}, status=500)



        
    # Handle Logout (Clears session)
@api_view(['POST'])
def logout(request):
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return Response({'status': False, 'message': 'Authentication required'}, status=401)
    
    user_token = UserToken.objects.filter(access_token=auth_header).first()
    if user_token:
        user_token.delete()  # token ko delete kar do
        return Response({'status': True, 'message': 'Logged out successfully'})
    
    return Response({'status': False, 'message': 'Invalid token'}, status=401)


# Forgot password 

# In-memory OTP storage
otp_store = {}
verified_users = set()  # ✅ OTP verify hone ke baad yaha store karenge


# Request OTP (Generate + Send Email)
@api_view(['POST'])
def request_otp(request):
    email = request.data.get("email")

    if not email:
        return Response({"status": False, "message": "Email required"}, status=400)

    user = UserProfile.objects.filter(user_email=email).first()
    if not user:
        return Response({"status": False, "message": "User not found"}, status=404)

    # ✅ OTP generate
    otp = random.randint(100000, 999999)
    expiry_time = time.time() + 300  # 5 minutes expiry
    otp_store[email] = (otp, expiry_time)

    # ✅ Send email
    send_mail(
        subject="Your OTP Code",
        message=f"Your OTP code is {otp}. It will expire in 5 minutes.",
        from_email="no-reply@cms.com",
        recipient_list=[email],
        fail_silently=False,
    )

    return Response({"status": True, "message": "OTP sent to your email"})


# Verify OTP
@api_view(['POST'])
def verify_otp_view(request):
    email = request.data.get("email")
    otp = request.data.get("otp")

    if not all([email, otp]):
        return Response({"status": False, "message": "Email and OTP required"}, status=400)

    if email in otp_store:
        stored_otp, expiry = otp_store[email]
        if time.time() > expiry:
            del otp_store[email]
            return Response({"status": False, "message": "OTP expired"}, status=400)

        if str(stored_otp) == str(otp):
            del otp_store[email]
            verified_users.add(email)  # ✅ Mark email as verified
            return Response({"status": True, "message": "OTP verified successfully"})

    return Response({"status": False, "message": "Invalid OTP"}, status=400)


# Reset Password
@api_view(['POST'])
def reset_password(request):
    email = request.data.get('email')
    new_password = request.data.get('new_password')
    confirm_password = request.data.get('confirm_password')

    # ✅ OTP verify check
    if email not in verified_users:
        return Response({'status': False, 'message': 'OTP verification required'}, status=403)

    if not all([email, new_password, confirm_password]):
        return Response({'status': False, 'message': 'All fields required'}, status=400)
    if new_password != confirm_password:
        return Response({'status': False, 'message': 'Passwords do not match'}, status=400)

    user = UserProfile.objects.filter(user_email=email).first()
    if not user:
        return Response({'status': False, 'message': 'User not found'}, status=404)

    user.password = make_password(new_password)
    user.save()

    # ✅ Reset ke baad verified list se hata do
    verified_users.discard(email)

    return Response({'status': True, 'message': 'Password updated successfully'}, status=200)
