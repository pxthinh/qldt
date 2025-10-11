from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views_admin as views

# Create a custom view that excludes from schema
class NoSchemaViewSet(views.OrderViewSet):
    def get_schema_fields(self, view):
        return []

# Use the default router but with our custom view
router = DefaultRouter()
router.register(r'admin/orders', NoSchemaViewSet, basename='admin-order')

# We'll handle order items within the OrderViewSet
urlpatterns = [
    path('', include(router.urls)),
]
