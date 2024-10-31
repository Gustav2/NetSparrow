from django.db import models
from django.contrib.auth.models import User

class Blacklist(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    ip = models.CharField(max_length=15)
    url = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.user.email} - {self.ip} - {self.url}"
