from django.db import models

class Business(models.Model):
    name = models.CharField(max_length=100, unique=True)
    email = models.EmailField()
    owner_name = models.CharField(max_length=100)
    is_approved = models.BooleanField(default=False)
    db_name = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


#Admin panel code

class SuperAdminToken(models.Model):
    token = models.CharField(max_length=255, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.token
