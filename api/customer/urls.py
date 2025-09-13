from django.urls import path
from .views import (
    customer_register, customer_confirm_email, customer_resend_confirmation
)
from .views_auth import (
    customer_login, customer_me, customer_logout
)
from .views_password import (
    password_reset_request, password_reset_confirm,
)

urlpatterns = [
    path('register/', customer_register, name='customer-register'),
    path('confirm/', customer_confirm_email, name='customer-confirm-email'),
    path('resend-confirmation/', customer_resend_confirmation, name='customer-resend-confirmation'),

    path('login/', customer_login, name='customer-login'),
    path('me/', customer_me, name='customer-me'),
    path('logout/', customer_logout, name='customer-logout'),

    path('password/reset/', password_reset_request, name='customer-password-reset-request'),
    path('password/reset/confirm/', password_reset_confirm, name='customer-password-reset-confirm'),
]
