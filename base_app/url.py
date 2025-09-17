from django.conf import settings
from django.urls import path
from . import views
from django.conf.urls.static import static

urlpatterns = [
    # URL for managing data without specifying item ID or field/value pair
    path('manage_data/<str:model_name>/', views.manage_data, name='manage_data'),

    # URL for managing data with a specific item ID
    path('manage_data/<str:model_name>/<int:item_id>/', views.manage_data, name='manage_data_detail'),

    # URL for managing data with a specific field and value
    path('manage_data/<str:model_name>/<str:field>/<str:value>/', views.manage_data, name='manage_data_field_value'),
    
    path('login/', views.login, name='login'),
    path('logout/', views.logout, name='logout'),
    path("signup/", views.signup, name="signup"),
    
    path('complaint/create/', views.create_complaint, name='create_complaint'),
    path("complaint/dropdown/<str:dropdown_type>/", views.dropdown_values, name="dropdown_values"),
    path('complaint/status/<str:complaint_code>/', views.complaint_status, name='complaint_status'),
    path('complaint/recent/', views.recent_complaints, name='recent_complaints'),
    path('complaint/recent/<int:complaint_id>/', views.complaint_detail, name='complaint_detail'),
    # path('complaint/view/<str:complaint_code>/', views.get_complaint_by_number, name='get_complaint_by_number'),
    path('complaint/nearby/', views.nearby_complaints, name='nearby_complaints'),

 # Forgot password flow
    path('api/request-otp/', views.request_otp, name='request-otp'),
    path('api/verify-otp/', views.verify_otp_view, name='verify-otp'),
    path('api/reset-password/', views.reset_password, name='reset-password'),
]
