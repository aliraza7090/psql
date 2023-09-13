"""eportal_back URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django_apscheduler.jobstores import register_events

# Import the SCHEDULER from the scheduler.py file
from .scheduler import SCHEDULER

# Register the scheduler events
register_events(SCHEDULER)

urlpatterns = [
    path("", include('health_check.urls')),
    path('admin/', admin.site.urls),
    path('api/auth/', include("accounts.urls.auth_urls")),
    path('api/users/', include("accounts.urls.user_urls")),
    path('api/profile/', include("accounts.urls.profile_urls")),
    path('api/leaves/', include("leaves.urls.leave_urls")),
    path('api/projects/', include("projects.urls.project_urls")),
]
