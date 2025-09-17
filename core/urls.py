from django.urls import path
from . import views

from .views import superadmin_login, superadmin_logout


urlpatterns = [
    path('register-business/', views.register_business, name='register-business'),
    
    #Admin panel code
    path('superadmin/login/', superadmin_login, name='superadmin_login'),
    path('superadmin/logout/', superadmin_logout, name='superadmin_logout'),
]