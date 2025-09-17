from django.db import models
from django.utils import timezone
from .constants import UserType

class UserProfile(models.Model):
    user_id = models.IntegerField(default=0, null=True, blank=True)
    user_name = models.CharField(max_length=100)
    user_type = models.CharField(max_length=20, default="CITIZEN")
    user_email = models.EmailField(unique=True)
    contact_number = models.CharField(max_length=20)
    password = models.CharField(max_length=128)
    address = models.TextField(max_length=100)
    city = models.CharField(max_length=100, null=True, blank=True)
    state = models.CharField(max_length=100, null=True, blank=True)
    created_by = models.IntegerField(null=True, blank=True)
    updated_by = models.IntegerField(null=True, blank=True)
    created_datetime = models.DateTimeField(auto_now_add=True)  # ✅ change here
    updated_datetime = models.DateTimeField(auto_now=True)      # ✅ change here

    def __str__(self):
        return self.user_name

    class Meta:
        db_table = "ms_user_profiles"

class UserToken(models.Model):
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    access_token = models.TextField()
    refresh_token = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.user_name} - Token"

    class Meta:
        db_table = "ms_user_token"

class QRCode(models.Model):
    code = models.CharField(max_length=255, unique=True)
    code_type = models.CharField(max_length=100)
    code_path = models.CharField(max_length=500, null=True, blank=True)
    isdeleted = models.BooleanField(default=False)
    created_date = models.DateTimeField(default=timezone.now)
    modified_date = models.DateTimeField(auto_now=True)
    isActive = models.BooleanField(default=True)
    reserver_1 = models.IntegerField(default=0)
    reserver_2 = models.CharField(max_length=255, null=True, blank=True)

class Complaint(models.Model):
    complaint_id = models.AutoField(primary_key=True)
    complaint_category = models.CharField(max_length=50)
    complaint_subcategory = models.CharField(max_length=50)
    complaint_code = models.CharField(max_length=20, unique=True, blank=True)
    zone = models.CharField(max_length=100)
    ward = models.CharField(max_length=100)
    description = models.TextField()
    landmark = models.CharField(max_length=200, blank=True)
    complaint_location = models.CharField(max_length=200)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    complaint_image = models.ImageField(upload_to='complaints/', null=True, blank=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    address1 = models.CharField(max_length=200)
    address2 = models.CharField(max_length=200, blank=True)
    area = models.CharField(max_length=100)
    mobile = models.CharField(max_length=15)
    email = models.EmailField()
    status = models.CharField(max_length=20, default='pending')
    share_publicly = models.BooleanField(default=False)
    created_by = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='complaints')
    created_datetime = models.DateTimeField(auto_now_add=True)
    updated_datetime = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.complaint_code:
            category_prefix = self.complaint_category[:3].upper()
            year = timezone.now().year
            last_id = Complaint.objects.count() + 1
            self.complaint_code = f"{category_prefix}-{year}-{last_id:04d}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.complaint_code} - {self.first_name} {self.last_name}"

    class Meta:
        db_table = "ms_complaints"

class ComplaintCategory(models.Model):
    name = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)

class ComplaintSubCategory(models.Model):
    category = models.ForeignKey(ComplaintCategory, on_delete=models.CASCADE, related_name="subcategories")
    name = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.category.name} - {self.name}"

class Zone(models.Model):
    name = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)

class Ward(models.Model):
    name = models.CharField(max_length=255)
    zone = models.ForeignKey(Zone, on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)
