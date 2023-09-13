from django.urls import path

from ..views import profile_views as views


urlpatterns = [
    path("", views.get_profile, name="get-profile"),
    path("update/", views.update_profile, name="update-profile"),
    path("change-password/", views.change_password, name="change-password"),
]
