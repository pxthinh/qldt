# api/customer/views_public.py
import json
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.core import signing
from django.core.mail import send_mail
from django.urls import reverse
from django.db.models import Q
from rest_framework.decorators import api_view
from rest_framework.response import Response
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .models import Customer
from .schemas import register_request, register_response

# Token configuration
TOKEN_SALT = "customer-email-confirm"
TOKEN_MAX_AGE = 60 * 60 * 24 * 3   # 3 days

def _json_body(request):
    try:
        return json.loads(request.body or "{}")
    except json.JSONDecodeError:
        return {}

def _build_confirm_url(request, token: str) -> str:
    path = reverse("customer-confirm-email")
    return request.build_absolute_uri(f"{path}?token={token}")

def _send_verification_email(request, customer: Customer):
    token = signing.dumps({"id": customer.pk, "email": customer.email}, salt=TOKEN_SALT)
    confirm_url = _build_confirm_url(request, token)
    subject = "Confirm your account"
    message = (
        f"Hello {customer.first_name or customer.user_name},\n\n"
        f"Please click the link below to confirm your email:\n{confirm_url}\n\n"
        f"This link is valid for 3 days."
    )
    send_mail(subject, message, None, [customer.email], fail_silently=False)

@swagger_auto_schema(
    method='post',
    tags=['Customer'],
    operation_summary="Register Customer",
    operation_description="Register a new customer account",
    request_body=register_request,
    responses=register_response
)
@api_view(['POST'])
@csrf_exempt
def customer_register(request):
    body = _json_body(request)

    user_name = (body.get("user_name") or "").strip()
    password  = (body.get("password") or "").strip()
    first_name = (body.get("first_name") or "").strip()
    last_name  = (body.get("last_name") or "").strip() or None
    email = (body.get("email") or "").strip().lower()
    phone = (body.get("phone") or "").strip() or None
    street = body.get("street") or None
    city   = body.get("city") or None
    state  = body.get("state") or None
    zip_code = body.get("zip_code") or None

    if not user_name:
        return JsonResponse({"detail": "user_name is required"}, status=400)
    if not password:
        return JsonResponse({"detail": "password is required"}, status=400)
    if not email:
        return JsonResponse({"detail": "email is required"}, status=400)

    if Customer.objects.filter(user_name__iexact=user_name).exists():
        return JsonResponse({"detail": "user_name already exists"}, status=400)
    if Customer.objects.filter(email__iexact=email).exists():
        return JsonResponse({"detail": "email already in use"}, status=400)

    obj = Customer(
        user_name=user_name,
        first_name=first_name,
        last_name=last_name,
        email=email,
        phone=phone,
        street=street, city=city, state=state, zip_code=zip_code,
        is_email_verified=False,
    )
    obj.set_password(password)
    obj.save()

    if obj.email:
        _send_verification_email(request, obj)

    return JsonResponse({
        "customer_id": obj.customer_id,
        "user_name": obj.user_name,
        "first_name": obj.first_name,
        "last_name": obj.last_name,
        "email": obj.email,
        "is_email_verified": obj.is_email_verified,
        "detail": "Registered. Please check your email to confirm."
    }, status=201)

@swagger_auto_schema(
    method='get',
    tags=['Customer'],
    operation_summary="Confirm Email",
    operation_description="Confirm customer email with verification token",
    responses={
        200: "Email confirmed successfully",
        400: "Invalid or expired token"
    }
)
@api_view(['GET'])
@require_http_methods(["GET"])
def customer_confirm_email(request):
    token = request.GET.get("token")
    if not token:
        return JsonResponse({"msg": "Token is required"}, status=400)
    try:
        data = signing.loads(token, salt=TOKEN_SALT, max_age=TOKEN_MAX_AGE)
    except signing.BadSignature:
        return JsonResponse({"msg": "Invalid token"}, status=400)
    except signing.SignatureExpired:
        return JsonResponse({"msg": "Token expired"}, status=400)

    cid = data.get("id")
    email = (data.get("email") or "").lower()
    try:
        obj = Customer.objects.get(pk=cid, email__iexact=email)
    except Customer.DoesNotExist:
        return JsonResponse({"msg": "Customer not found"}, status=404)

    if obj.is_email_verified:
        return JsonResponse({"msg": "Email already verified"})

    obj.is_email_verified = True
    obj.save(update_fields=["is_email_verified"])
    return JsonResponse({"msg": "Email verified successfully"})

@swagger_auto_schema(
    method='post',
    tags=['Customer'],
    operation_summary="Resend Confirmation",
    operation_description="Resend email confirmation",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        required=['email'],
        properties={
            'email': openapi.Schema(type=openapi.TYPE_STRING, format='email')
        }
    ),
    responses={
        200: "Confirmation email resent",
        400: "Invalid email or user already verified"
    }
)
@api_view(['POST'])
@csrf_exempt
@require_http_methods(["POST"])
def customer_resend_confirmation(request):
    body = _json_body(request)
    user_name = (body.get("user_name") or "").strip()
    email = (body.get("email") or "").strip().lower()

    if not user_name and not email:
        return JsonResponse({"detail": "user_name or email is required"}, status=400)

    try:
        if user_name:
            obj = Customer.objects.get(user_name__iexact=user_name)
        else:
            obj = Customer.objects.get(email__iexact=email)
    except Customer.DoesNotExist:
        return JsonResponse({"detail": "If the account exists, an email has been sent."})

    if not obj.email:
        return JsonResponse({"detail": "Account has no email to send to"}, status=400)

    if obj.is_email_verified:
        return JsonResponse({"detail": "email already verified"})

    _send_verification_email(request, obj)
    return JsonResponse({"detail": "Verification email sent"})
