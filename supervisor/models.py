
from django.db import models
from base_app.models import SupervisorProfile


class SupervisorToken(models.Model):
    supervisor = models.ForeignKey(SupervisorProfile, on_delete=models.CASCADE)
    access_token = models.TextField()
    refresh_token = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.supervisor.user_email} - Token"

    class Meta:
        db_table = "ms_supervisor_token"