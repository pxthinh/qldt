from django.urls import path
from .views import ProductListAPIView

urlpatterns = [
    # Public endpoints
    path('', ProductListAPIView.as_view(), name='product-list'),
]