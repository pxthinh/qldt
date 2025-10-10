from django.urls import path
from .views_admin import product_admin_list, product_admin_detail

app_name = 'product_admin'

urlpatterns = [
    # Admin endpoints
    path('', product_admin_list, name='product-list'),
    path('<int:id>/', product_admin_detail, name='product-detail'),
]