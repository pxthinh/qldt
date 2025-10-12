from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import (
    customer_register, customer_confirm_email, customer_resend_confirmation
)
from .views_auth import (
    CustomerLoginView, CustomerProfileView, CustomerLogoutView,
    CustomerUpdateProfileView, CustomerUpdatePasswordView
)
from .views_password import (
    password_reset_request, password_reset_confirm,
)

# Create a router for class-based views
router = DefaultRouter()

urlpatterns = [
    # Authentication endpoints
    path('login/', CustomerLoginView.as_view(), name='customer-login'),
    path('me/', CustomerProfileView.as_view(), name='customer-me'),
    path('logout/', CustomerLogoutView.as_view(), name='customer-logout'),

    # Registration endpoints
    path('register/', customer_register, name='customer-register'),
    path('confirm/', customer_confirm_email, name='customer-confirm-email'),
    path('resend-confirmation/', customer_resend_confirmation, name='customer-resend-confirmation'),

    # Profile endpoints
    path('me/update/', CustomerUpdateProfileView.as_view(), name='customer-update-profile'),
    path('me/update-password/', CustomerUpdatePasswordView.as_view(), name='customer-update-password'),

    # Password reset endpoints
    path('password/reset/', password_reset_request, name='customer-password-reset-request'),
    path('password/reset/confirm/', password_reset_confirm, name='customer-password-reset-confirm'),
]

urlpatterns += router.urls
