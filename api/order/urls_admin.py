from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views_admin import OrderAdminViewSet

app_name = 'admin_orders'

# Create a router and register our viewsets with it
router = DefaultRouter()
router.register(r'', OrderAdminViewSet, basename='admin-order')

# The API URLs are now determined automatically by the router
urlpatterns = [
    path('', include(router.urls)),
]
