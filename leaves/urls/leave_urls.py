from django.urls import path

from ..views import leave_views as views


urlpatterns = [
    path("", views.get_leaves, name="get-leaves"),
    path("create/", views.create_leave, name="create-leave"),
    path("update/<str:id>", views.update_leave, name="update-leave"),
]
