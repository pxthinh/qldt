from django.urls import path
from .views_admin import order_admin_list, order_admin_detail

app_name = 'admin_orders'

urlpatterns = [
    path("", order_admin_list, name="admin-order-list"),
    path("<int:id>/", order_admin_detail, name="admin-order-detail"),
]
