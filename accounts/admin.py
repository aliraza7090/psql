from django.contrib import admin

from .models import User, HubStaffConfig, AvazaConfig

# Register your models here.

admin.site.register(User)
admin.site.register(HubStaffConfig)
admin.site.register(AvazaConfig)
