from django.urls import path
from . import views_admin

urlpatterns = [
    # Public endpoints
    path('', views_admin.dashboard_statistics, name='dashboard_statistics'),
    path('system', views_admin.system_health, name='system_health'),
]