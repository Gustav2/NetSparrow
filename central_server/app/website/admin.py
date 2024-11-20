from django.contrib import admin
from .models import Blacklist, MyBlacklist, CapturedPacket

admin.site.register(Blacklist)
admin.site.register(MyBlacklist)
admin.site.register(CapturedPacket)

# Register your models here.
