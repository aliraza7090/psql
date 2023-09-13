from django.urls import path

from ..views import auth_views as views


urlpatterns = [
    path('login/', views.MyTokenObtainPairView.as_view(), name="login"),
    path('forget/', views.forget_password, name="forget-password"),
    path('reset/', views.reset_password, name="reset-password"),
]
