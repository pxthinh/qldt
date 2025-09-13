from django.urls import path
from .views_admin import brand_admin_list, brand_admin_detail

urlpatterns = [
    path("", brand_admin_list, name="admin-brand-list"),
    path("<int:id>/", brand_admin_detail, name="admin-brand-detail"),
]