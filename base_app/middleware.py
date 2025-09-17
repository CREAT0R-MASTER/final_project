from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin
from .models import UserToken 
from django.urls import resolve

class TokenAuthMiddleware(MiddlewareMixin):
    def process_request(self, request):

        if request.path.startswith('/admin/'):
            return None

        # Get the current URL path
        current_path = resolve(request.path_info).url_name  
        print("current_path in middleware is ",current_path)

        # Define allowed endpoints (without authentication)
        exempt_routes = ["signup","login","logout","register-business"]

        if current_path in exempt_routes:
            return None 
        else:
            # Extract token from the request header
            token = request.headers.get("Authorization")
            print("token in middleware is ",token)
            
            if not token:
                return JsonResponse({"error": "Unauthorized - Token missing"}, status=401)
            # Check if the token exists in the UserToken table
            if not UserToken.objects.filter(access_token=token).exists():
                return JsonResponse({"error": "Unauthorized - Invalid Token"}, status=401)

        # Token is valid, allow request to continue
        return None
