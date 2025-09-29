from django.db import models
from django.utils import timezone

# --------------------- USER PROFILE ---------------------
class UserProfile(models.Model):
    # Django automatically primary key 'id' banata hai
    user_name = models.CharField(max_length=100)
    user_type = models.CharField(max_length=20, default="CITIZEN")  # CITIZEN / ADMIN / SUPERVISOR
    user_email = models.EmailField(unique=True)
    contact_number = models.CharField(max_length=20)
    password = models.CharField(max_length=128)
    address = models.CharField(max_length=100)
    city = models.CharField(max_length=100, null=True, blank=True)
    state = models.CharField(max_length=100, null=True, blank=True)
    created_by = models.IntegerField(null=True, blank=True)
    updated_by = models.IntegerField(null=True, blank=True)
    created_datetime = models.DateTimeField(default=timezone.now, null=True, blank=True)
    updated_datetime = models.DateTimeField(default=timezone.now, null=True, blank=True)


    def __str__(self):
        return self.user_name

    class Meta:
        db_table = "ms_user_profiles"

# --------------------- USER TOKEN ---------------------
class UserToken(models.Model):
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    access_token = models.TextField()
    refresh_token = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.user_name} - Token"

    class Meta:
        db_table = "ms_user_token"

# --------------------- QR CODE ---------------------
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

# --------------------- ZONE ---------------------
class Zone(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20, unique=True)
    is_active = models.BooleanField(default=True)  # ✅ Add this line


    def __str__(self):
        return f"{self.name} ({self.code})"

# --------------------- WARD ---------------------
class Ward(models.Model):
    name = models.CharField(max_length=100)
    zone = models.ForeignKey(Zone, on_delete=models.CASCADE, related_name='wards')
    is_active = models.BooleanField(default=True)


    def __str__(self):
        return f"{self.name} - {self.zone.name}"

# --------------------- COMPLAINT CATEGORY ---------------------
class ComplaintCategory(models.Model):
    name = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

# --------------------- COMPLAINT SUBCATEGORY ---------------------
class ComplaintSubCategory(models.Model):
    category = models.ForeignKey(ComplaintCategory, on_delete=models.CASCADE, related_name="subcategories")
    name = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.category.name} - {self.name}"

# --------------------- COMPLAINT ---------------------
class Complaint(models.Model):
    complaint_id = models.AutoField(primary_key=True)
    complaint_category = models.ForeignKey(ComplaintCategory, on_delete=models.SET_NULL, null=True)
    complaint_subcategory = models.ForeignKey(ComplaintSubCategory, on_delete=models.SET_NULL, null=True)
    complaint_code = models.CharField(max_length=20, unique=True, blank=True)
    zone = models.ForeignKey(Zone, on_delete=models.SET_NULL, null=True)
    ward = models.ForeignKey(Ward, on_delete=models.SET_NULL, null=True)
    description = models.TextField()
    landmark = models.CharField(max_length=200, blank=True)
    complaint_location = models.CharField(max_length=200)
    latitude = models.FloatField(null=True, blank=True, unique=True)
    longitude = models.FloatField(null=True, blank=True, unique=True)
    complaint_image = models.ImageField(upload_to='complaints/', null=True, blank=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    address1 = models.CharField(max_length=200)
    address2 = models.CharField(max_length=200, blank=True)
    area = models.CharField(max_length=100)
    mobile = models.CharField(max_length=15)
    email = models.EmailField()
    status = models.CharField(max_length=20, default='pending')
    share_publicly = models.BooleanField(default=True)
    created_by = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='complaints', null=True, blank=True)
    assigned_supervisor = models.ForeignKey('SupervisorProfile', on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_complaints')
    created_datetime = models.DateTimeField(default=timezone.now, null=True, blank=True)
    updated_datetime = models.DateTimeField(default=timezone.now, null=True, blank=True)
    resolved_image = models.ImageField(upload_to='complaints/resolved/', null=True, blank=True)
    resolved_datetime = models.DateTimeField(null=True, blank=True)
    resolved_by = models.ForeignKey('SupervisorProfile', on_delete=models.SET_NULL, null=True, blank=True, related_name='resolved_complaints')



    def save(self, *args, **kwargs):
        if not self.complaint_code:
            category_prefix = self.complaint_category.name[:3].upper() if self.complaint_category else "COM"
            year = timezone.now().year
            last_id = Complaint.objects.count() + 1
            self.complaint_code = f"{category_prefix}-{year}-{last_id:04d}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.complaint_code} - {self.first_name} {self.last_name}"

    class Meta:
        db_table = "ms_complaints"

# --------------------- SUPERVISOR PROFILE ---------------------
class SupervisorProfile(models.Model):
    user_name = models.CharField(max_length=100)
    user_type = models.CharField(max_length=20, default="SUPERVISOR")
    user_email = models.EmailField(unique=True)
    contact_number = models.CharField(max_length=20)
    password = models.CharField(max_length=128)  # Admin will save generated password
    address = models.CharField(max_length=100)
    city = models.CharField(max_length=100, null=True, blank=True)
    state = models.CharField(max_length=100, null=True, blank=True)
    zone = models.ForeignKey(Zone, on_delete=models.SET_NULL, null=True, blank=True, related_name="supervisors")
    ward = models.ForeignKey(Ward, on_delete=models.SET_NULL, null=True, blank=True, related_name="supervisors")
    profile_image = models.ImageField(upload_to='supervisors/', null=True, blank=True)
    created_by = models.IntegerField(null=True, blank=True)
    updated_by = models.IntegerField(null=True, blank=True)
    created_datetime = models.DateTimeField(default=timezone.now)
    updated_datetime = models.DateTimeField(default=timezone.now)


    def __str__(self):
        return f"{self.user_name} ({self.user_type})"

    class Meta:
        db_table = "ms_supervisor_profiles"
