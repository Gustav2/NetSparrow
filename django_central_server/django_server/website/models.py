from django.db import models

class Blacklist(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    email = models.EmailField(max_length=255)
    ip = models.CharField(max_length=15)
    url = models.CharField(max_length=255)

    def __str__(self):
        return (f"{self.ip} - {self.url}")
