from django.contrib import admin
from .models import Blacklist, MyBlacklist, CapturedPacket, MySettings

admin.site.register(Blacklist)
admin.site.register(MyBlacklist)
admin.site.register(CapturedPacket)
admin.site.register(MySettings)

# Register your models here.
