from django.urls import path
from . import views

urlpatterns = [
    path("login/", views.supervisor_login, name="supervisor_login"),  # ✅ Exact match with middleware
    path("logout/", views.supervisor_logout, name="supervisor_logout"),  # ✅ Logout added
    
    path("assigned-complaints/", views.assigned_complaints, name="assigned_complaints"),
    path('resolve-complaint/', views.resolve_complaint, name='resolve_complaint'),


]
