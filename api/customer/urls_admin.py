from django.urls import path
from rest_framework.routers import DefaultRouter
from api.customer.views_admin import CustomerAdminListCreate, CustomerAdminDetail

# Create a router for ViewSets
router = DefaultRouter()

# Register views with the router
urlpatterns = [
    path('', CustomerAdminListCreate.as_view(), name='admin-customer-list'),
    path('<int:pk>/', CustomerAdminDetail.as_view(), name='admin-customer-detail'),
]

# Include router URLs
urlpatterns += router.urls
