from django.urls import path
from .views_admin import customer_admin_list, customer_admin_detail

urlpatterns = [
    path('', customer_admin_list, name='admin-customer-list'),
    path('<int:id>/', customer_admin_detail, name='admin-customer-detail'),
]
