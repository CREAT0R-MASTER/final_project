# core/models.py
from django.utils import timezone  # ✅ Add this import
from django.db import models
from django.contrib.auth.hashers import make_password


class Business(models.Model):
    name = models.CharField(max_length=100, unique=True)
    email = models.EmailField()
    owner_name = models.CharField(max_length=100)
    is_approved = models.BooleanField(default=False)
    db_name = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class AdminUser(models.Model):
    user_name = models.CharField(max_length=255)
    user_email = models.EmailField(unique=True)
    contact_number = models.CharField(max_length=20)
    password = models.CharField(max_length=255)
    user_type = models.CharField(max_length=50, default="ADMIN")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def set_password(self, raw_password):
        self.password = make_password(raw_password)
        self.save()

    def __str__(self):
        return self.user_email


class AdminToken(models.Model):
    admin = models.ForeignKey(AdminUser, on_delete=models.CASCADE)
    access_token = models.TextField()
    refresh_token = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(default=timezone.now)  # ✅ Add this line


    def __str__(self):
        return f"{self.admin.user_email} - Token"

    class Meta:
        db_table = "ms_admin_token"