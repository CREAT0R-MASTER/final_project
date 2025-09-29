# core/serializers.py
from rest_framework import serializers
from .models import Business, AdminUser

class BusinessSerializer(serializers.ModelSerializer):
    class Meta:
        model = Business
        fields = '__all__'
        read_only_fields = ['is_approved', 'db_name', 'created_at']

class AdminUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = AdminUser
        fields = ["id", "user_name", "user_email", "contact_number", "user_type", "created_at", "updated_at"]