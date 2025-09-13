from django.urls import path
from .views_admin import category_admin_list, category_admin_detail

urlpatterns = [
    path("", category_admin_list, name="admin-category-list"),
    path("<int:id>/", category_admin_detail, name="admin-category-detail"),
]