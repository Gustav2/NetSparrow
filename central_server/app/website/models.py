from django.db import models
from django.contrib.auth.models import User
from django.db.models import UniqueConstraint
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.exceptions import ValidationError

class Blacklist(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    capturedpacket_entry = models.ForeignKey('CapturedPacket', on_delete=models.SET_NULL, null=True)

    def __str__(self):
        if self.capturedpacket_entry:
            return f"{self.capturedpacket_entry.ip or None} - {self.capturedpacket_entry.url or None}"
        return "Orphaned Blacklist Entry"

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)

        if is_new:
            users_with_auto_add = MySettings.objects.filter(auto_add_blacklist=True).values_list('user', flat=True)
            for user_id in users_with_auto_add:
                MyBlacklist.objects.get_or_create(user_id=user_id, blacklist_entry=self)


class MyBlacklist(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    blacklist_entry = models.ForeignKey('Blacklist', on_delete=models.CASCADE)
    added_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    class Meta:
        constraints = [
            UniqueConstraint(fields=['blacklist_entry', 'user'], name='unique_blacklist_user')
        ]

    def __str__(self):
        return f"{self.user.username if self.user else 'No User'}'s entry: {self.blacklist_entry}"


class CapturedPacket(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    captured_at = models.DateTimeField(auto_now_add=True)
    ip = models.CharField(max_length=15, null=True, blank=True)
    url = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        unique_together = ('user', 'ip', 'url')

    def clean(self):
        if not self.ip and not self.url:
            raise ValidationError("At least one of IP or URL must be provided.")
        if self.ip == "130.225.37.168":
            raise ValidationError("You cannot add this IP.")

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.ip} - {self.url}"

@receiver(post_save, sender=CapturedPacket)
def check_capture_count(sender, instance, **kwargs):
    capture_count = CapturedPacket.objects.filter(ip=instance.ip, url=instance.url).values('user').distinct().count()

    if capture_count >= 1:
        if not Blacklist.objects.filter(capturedpacket_entry__ip=instance.ip, capturedpacket_entry__url=instance.url).exists():
            captured_packet_entry = CapturedPacket.objects.filter(ip=instance.ip, url=instance.url).first()
            Blacklist.objects.create(capturedpacket_entry=captured_packet_entry)

class MySettings(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='settings')
    auto_add_blacklist = models.BooleanField(default=False)
    log_suspicious_packets = models.BooleanField(default=False)
    enable_ip_blocking = models.BooleanField(default=False)
    dark_mode = models.BooleanField(default=False)
    notify_blacklist_updates = models.BooleanField(default=False)
    notify_suspicious_activity = models.BooleanField(default=False)
    ml_caution = models.DecimalField(max_digits=1, decimal_places=1,default=0.9)
    ml_percentage = models.IntegerField(default=100)

    def __str__(self):
        return f"Settings for {self.user.username}"
