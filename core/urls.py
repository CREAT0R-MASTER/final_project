from django.urls import path
from . import views

from .views import admin_login, admin_logout, admin_signup, complaint_category_api, complaint_subcategory_api, ward_api, zone_api


urlpatterns = [
    path('register-business/', views.register_business, name='register-business'),
    
    #Admin panel code
    path('admin/signup/', admin_signup, name='admin_signup'),
    path('admin/login/', admin_login, name='admin_login'),
    path('admin/logout/', admin_logout, name='admin_logout'),
    
    # Complaint Category
    path('admin/category/', views.complaint_category_api, name='complaint_category_list'),
    path('admin/category/<int:pk>/', views.complaint_category_api, name='complaint_category_detail'),

    # Complaint SubCategory
    path('admin/subcategory/', views.complaint_subcategory_api, name='complaint_subcategory_list'),
    path('admin/subcategory/<int:pk>/', views.complaint_subcategory_api, name='complaint_subcategory_detail'),

    # Zone CRUD
    path('admin/zone/', zone_api, name='zone_list_create'),          # GET all zones, POST create zone
    path('admin/zone/<int:pk>/', zone_api, name='zone_detail_update_delete'),  # GET, PUT, DELETE specific zone

    # Ward CRUD
    path('admin/ward/', ward_api, name='ward_list_create'),          # GET all wards, POST create ward
    path('admin/ward/<int:pk>/', ward_api, name='ward_detail_update_delete'),  # GET, PUT, DELETE specific ward
    # Complaint Management
    path('admin/complaints/', views.complaint_management_api, name='complaints_list'),
    path('admin/complaints/<int:pk>/', views.complaint_management_api, name='complaint_detail'),

    # Dashboard
    path('admin/dashboard/', views.dashboard_statistics, name='dashboard_statistics'),
    
    # Supervisor API
    path('admin/supervisors/', views.supervisor_api, name='supervisor-list'),          # GET list, POST create
    path('admin/supervisors/<int:pk>/', views.supervisor_api, name='supervisor-detail') # GET single, PUT update, DELETE

]