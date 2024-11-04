from django.contrib import admin
from .models import Blacklist, MyBlacklist

admin.site.register(Blacklist)
admin.site.register(MyBlacklist)

# Register your models here.
