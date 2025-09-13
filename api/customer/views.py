# api/customer/views_public.py
import json
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.core import signing
from django.core.mail import send_mail
from django.urls import reverse
from django.db.models import Q
from .models import Customer

# cấu hình token
TOKEN_SALT = "customer-email-confirm"
TOKEN_MAX_AGE = 60 * 60 * 24 * 3   # 3 ngày

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
    subject = "Xác nhận tài khoản của bạn"
    message = (
        f"Chào {customer.first_name or customer.user_name},\n\n"
        f"Nhấn vào liên kết dưới đây để xác nhận email:\n{confirm_url}\n\n"
        f"Liên kết có hiệu lực trong 3 ngày."
    )
    send_mail(subject, message, None, [customer.email], fail_silently=False)

@csrf_exempt
@require_http_methods(["POST"])
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

@require_http_methods(["GET"])
def customer_confirm_email(request):
    token = request.GET.get("token")
    if not token:
        return JsonResponse({"detail": "token is required"}, status=400)
    try:
        data = signing.loads(token, salt=TOKEN_SALT, max_age=TOKEN_MAX_AGE)
    except signing.BadSignature:
        return JsonResponse({"detail": "invalid token"}, status=400)
    except signing.SignatureExpired:
        return JsonResponse({"detail": "token expired"}, status=400)

    cid = data.get("id")
    email = (data.get("email") or "").lower()
    try:
        obj = Customer.objects.get(pk=cid, email__iexact=email)
    except Customer.DoesNotExist:
        return JsonResponse({"detail": "customer not found"}, status=404)

    if obj.is_email_verified:
        return JsonResponse({"detail": "email already verified"})

    obj.is_email_verified = True
    obj.save(update_fields=["is_email_verified"])
    return JsonResponse({"detail": "email verified successfully"})

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
