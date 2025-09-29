from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin
from django.urls import resolve
from django.utils import timezone

from supervisor.models import SupervisorToken
from .models import UserToken
from core.models import AdminToken

from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin
from django.urls import resolve
from django.utils import timezone
from .models import UserToken  

class TokenAuthMiddleware(MiddlewareMixin):
    def process_request(self, request):
        # ✅ Skip admin routes
        if request.path.startswith('/core_api/'):
            return None
            
        # ✅ Skip supervisor routes
        if request.path.startswith('/supervisor/'):
            print(f"🔄 User middleware skipping supervisor route: {request.path}")
            return None

        # ✅ Exempt routes (user) - ye routes jahan token ki jarurat nahi
        exempt_routes_names = ["signup", "login", "logout", "register-business", "request-otp", "verify-otp", "reset-password", "states_api", "cities_api",""]
        exempt_routes_paths = ["/api/login/", "/api/signup/", "/api/logout/"]

        try:
            print("in user middleware - for user routes only")
            current_path = resolve(request.path_info).url_name
        except Exception:
            current_path = None

        # ✅ Agar route exempt hai toh token check nahi karenge
        if current_path in exempt_routes_names or request.path in exempt_routes_paths:
            return None

        # ✅ Token check ONLY for user routes
        token = request.headers.get("Authorization")
        print("User middleware - Request Path:", request.path)
        if not token:
            return JsonResponse({"error": "Unauthorized - Token missing"}, status=401)

        # ✅ Remove "Bearer " prefix from token
        token = token.replace("Bearer ", "").strip()
        
        try:
            # ✅ FIXED: Check if expires_at field exists in model
            # Pehle check karenge ki model mein expires_at field hai ya nahi
            if hasattr(UserToken, 'expires_at'):
                # ✅ Agar expires_at field hai toh expiry check karenge
                token_obj = UserToken.objects.filter(
                    access_token=token,
                    expires_at__gt=timezone.now()  # Check if token is not expired
                ).first()
            else:
                # ✅ Agar expires_at field nahi hai toh sirf token existence check karenge
                token_obj = UserToken.objects.filter(access_token=token).first()
                print("ℹ️ Token expiry check skipped - expires_at field not found in model")
            
            if not token_obj:
                return JsonResponse({"error": "Unauthorized - Invalid Token"}, status=401)
                
            # ✅ Attach user to request for easy access in views
            request.user_token = token_obj
            print(f"✅ User authenticated: {token_obj.user.user_name}")
            
        except Exception as e:
            print(f"❌ User token validation error: {str(e)}")
            return JsonResponse({"error": "Token validation failed"}, status=401)

        return None

class AdminTokenAuthMiddleware(MiddlewareMixin):
    def process_request(self, request):
        # ✅ DEBUG: Pehle check karte hain kya path aa raha hai
        print(f"🔍 Admin Middleware - Path: {request.path}")
        
        # ✅ CORRECTED: Admin routes identify karo
        # Tumhare URLs mein '/admin/' se start hone wale routes admin routes hain
        # Aur public routes hain: /login/, /signup/, /logout/, /register-business/
        is_admin_route = request.path.startswith('/admin/')
        is_public_route = request.path in ['/login/', '/signup/', '/logout/', '/register-business/']
        
        # ✅ Agar na admin route hai na public route, toh return None
        if not is_admin_route and not is_public_route:
            print(f"❌ Not an admin or public route: {request.path}")
            return None

        # ✅ CORRECTED: Exempt public routes (inhe token ki jarurat nahi)
        exempt_routes_names = ["admin_login", "admin_logout", "admin_signup", "register-business"]
        exempt_routes_paths = ["/login/", "/signup/", "/logout/", "/register-business/"]

        try:
            current_path = resolve(request.path_info).url_name
            print(f"🔖 Route Name: {current_path}")
        except Exception as e:
            print(f"❌ Route resolve error: {e}")
            current_path = None

        # ✅ Agar route exempt hai toh token check nahi karenge
        if current_path in exempt_routes_names or request.path in exempt_routes_paths:
            print(f"✅ Route exempted: {request.path}")
            return None

        # ✅ Token check ONLY for protected admin routes (/admin/ wale routes)
        token = request.headers.get("Authorization")
        print(f"🔑 Token present: {bool(token)}")
        
        if not token:
            print(f"❌ Token missing for protected admin route: {request.path}")
            return JsonResponse({"error": "Unauthorized - Token missing"}, status=401)

        token = token.replace("Bearer ", "").strip()
        
        try:
            # ✅ Token validation with expiry check
            token_obj = AdminToken.objects.filter(
                access_token=token,
                expires_at__gt=timezone.now()
            ).first()
            
            if not token_obj:
                print("❌ Invalid or expired token")
                return JsonResponse({"error": "Unauthorized - Invalid or expired Token"}, status=401)
                
            # ✅ Attach admin to request for easy access in views
            request.admin_token = token_obj
            print(f"✅ Admin authenticated: {token_obj.admin.user_email}")
            
        except Exception as e:
            print(f"❌ Admin token validation error: {str(e)}")
            return JsonResponse({"error": "Token validation failed"}, status=401)

        return None

class SupervisorTokenAuthMiddleware(MiddlewareMixin):
    def process_request(self, request):
        # ✅ Only supervisor routes
        if not request.path.startswith('/supervisor/'):
            return None

        # ✅ Exempt routes - FIXED: removed "supervisor_signup" since it doesn't exist in your URLs
        exempt_routes_names = ["supervisor_login", "supervisor_logout"]  # ❌ REMOVED: "supervisor_signup"
        exempt_routes_paths = ["/supervisor/login/", "/supervisor/logout/"]

        try:
            current_path = resolve(request.path_info).url_name
        except Exception:
            current_path = None

        print(f"🔍 Supervisor Middleware - Path: {request.path}, Route Name: {current_path}")

        if current_path in exempt_routes_names or request.path in exempt_routes_paths:
            # ✅ Login/logout me token ki jarurat nahi
            print(f"✅ Exempted supervisor route: {request.path} - No token required")
            return None

        # ✅ Token check for protected routes only
        token = request.headers.get("Authorization")
        print(f"🔑 Token check for: {request.path}, Token present: {bool(token)}")
        
        if not token:
            return JsonResponse({"error": "Unauthorized - Token missing"}, status=401)

        # Remove "Bearer " prefix if present
        token = token.replace("Bearer ", "").strip()

        try:
            # ✅ CORRECT FIELD NAME: access_token with expiry check
            token_qs = SupervisorToken.objects.select_related('supervisor').filter(
                access_token=token,
                expires_at__gt=timezone.now()  # Token expiry check
            )
            print(f"🔎 Token found in DB: {token_qs.exists()}")
            
            if not token_qs.exists():
                return JsonResponse({"error": "Unauthorized - Invalid or expired Token"}, status=401)

            # ✅ Attach supervisor to request for easy access in views
            token_obj = token_qs.first()
            request.supervisor = token_obj.supervisor
            print(f"✅ Token valid for supervisor: {request.supervisor.user_email}")
            
        except Exception as e:
            print(f"❌ Token validation error: {str(e)}")
            return JsonResponse({"error": "Token validation failed"}, status=401)

        return None