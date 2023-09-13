from django.urls import path

from ..views import project_views as views

urlpatterns = [
    path("sync/", views.sync_projects, name="sync-projects"),
    path("", views.get_projects, name="get-projects"),
    path("self/", views.get_my_projects, name="get-my-projects"),
    path('create/', views.create_project, name="create-project"),
    path("update-member/", views.update_project_member,
         name="update-project-member"),
    path('<str:id>', views.get_project_by_id, name="get-project-by-id"),
]
