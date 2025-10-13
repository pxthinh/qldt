from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'', views.StoreViewSet, basename='admin-store')

app_name = 'store-admin'

urlpatterns = [
    path('', include(router.urls)),
]
