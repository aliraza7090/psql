from django.contrib import admin

from .models import Leave, LeaveStatistic

# Register your models here.

admin.site.register(Leave)
admin.site.register(LeaveStatistic)
