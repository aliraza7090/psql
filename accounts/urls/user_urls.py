from django.urls import path

from ..views import user_views as views


urlpatterns = [
    path("", views.get_users, name="get-users"),
    path("delete/", views.delete_user, name="delete-user"),
    path("create/", views.create_user, name="create-user"),
    path("edit/<str:id>", views.edit_user, name="edit-user"),
    path("<str:id>", views.get_user_by_id, name="get-user-by-id"),
]
