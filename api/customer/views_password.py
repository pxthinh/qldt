import json
import time
from datetime import datetime, timedelta
from django.utils import timezone
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponseNotAllowed
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.core import signing
from django.core.mail import send_mail
from django.urls import reverse
from django.conf import settings
from rest_framework.decorators import api_view
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .models import Customer
from .schemas import (
    password_reset_request_schema,
    password_reset_confirm_schema,
    password_reset_response
)

# Token configuration
TOKEN_SALT = "customer-password-reset"
TOKEN_MAX_AGE = 60 * 60 * 24  # 1 day

def _json_body(request):
    try:
        return json.loads(request.body or "{}")
    except json.JSONDecodeError:
        return {}

def _build_reset_url(request, token: str) -> str:
    path = reverse("customer-password-reset-confirm")
    return request.build_absolute_uri(f"{path}?token={token}")

def _send_reset_email(request, customer: Customer):
    subject = "Reset Your Password"
    token = signing.dumps({"id": customer.pk, "email": (customer.email or "").lower(), "ts": int(time.time())},
                          salt=TOKEN_SALT)
    url = _build_reset_url(request, token)
    message = (
        f"Hello {customer.first_name or customer.user_name},\n\n"
        f"You have requested to reset your password. Click the link below to set a new password "
        f"(valid for 1 hour):\n{url}\n\n"
        f"If you didn't request this, please ignore this email."
    )
    send_mail(subject, message, None, [customer.email], fail_silently=False)

@swagger_auto_schema(
    method='post',
    tags=['Customer'],
    operation_summary="Request Password Reset",
    operation_description="Request a password reset email",
    request_body=password_reset_request_schema,
    responses=password_reset_response
)
@api_view(['POST'])
@csrf_exempt
@require_http_methods(["POST"])
def password_reset_request(request):
    """
    Send password reset email (if email exists).
    """
    body = _json_body(request)
    user_name = (body.get("user_name") or "").strip()
    email = (body.get("email") or "").strip().lower()

    try:
        if user_name:
            obj = Customer.objects.get(user_name__iexact=user_name)
        elif email:
            obj = Customer.objects.get(email__iexact=email)
        else:
            return JsonResponse({"detail": "user_name or email is required"}, status=400)

        if obj.email:
            _send_reset_email(request, obj)
    except Customer.DoesNotExist:
        pass

    return JsonResponse({"detail": "If the email exists, a password reset link has been sent"})

@swagger_auto_schema(
    method='post',
    tags=['Customer'],
    operation_summary="Reset Password",
    operation_description="Reset password with a valid token",
    request_body=password_reset_confirm_schema,
    responses=password_reset_response
)
@api_view(['POST'])
@csrf_exempt
@require_http_methods(["POST"])
def password_reset_confirm(request):
    """
    Reset password with a valid token.
    """
    body = _json_body(request)

    token = body.get("token") or request.GET.get("token")
    new_password = (body.get("new_password") or "").strip()
    confirm_password = (body.get("confirm_password") or body.get("password_confirm") or "").strip()

    if not token:
        return JsonResponse({"detail": "token is required"}, status=400)
    if not new_password or len(new_password) < 6:
        return JsonResponse({"detail": "new_password must be at least 6 characters"}, status=400)
    if not confirm_password:
        return JsonResponse({"detail": "confirm_password is required"}, status=400)
    if new_password != confirm_password:
        return JsonResponse({"detail": "password confirmation does not match"}, status=400)

    try:
        data = signing.loads(token, salt=TOKEN_SALT, max_age=TOKEN_MAX_AGE)
        cid = data.get("id")
        email = (data.get("email") or "").lower()
        obj = Customer.objects.get(pk=cid)

        if obj.email and obj.email.lower() != email:
            return JsonResponse({"detail": "invalid token"}, status=400)
    except signing.SignatureExpired:
        return JsonResponse({"detail": "token expired"}, status=400)
    except (signing.BadSignature, Customer.DoesNotExist):
        return JsonResponse({"detail": "invalid token"}, status=400)

    obj.set_password(new_password)
    obj.save(update_fields=["password"])

    return JsonResponse({"detail": "Password updated successfully"})
