from django.urls import path
from . import views

urlpatterns = [
    # Public endpoints
    path('', views.get_all, name='product-list'),
]