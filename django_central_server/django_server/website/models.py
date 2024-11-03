from django.db import models
from django.contrib.auth.models import User

class Blacklist(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    ip = models.CharField(max_length=15, blank=True, null=True)
    url = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f"{self.ip} - {self.url}"

class MyBlacklist(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    blacklist_entry = models.ForeignKey('Blacklist', on_delete=models.CASCADE)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'blacklist_entry')  # Prevents duplicates for the same user

    def __str__(self):
        return f"{self.user.username}'s entry: {self.blacklist_entry}"
    

