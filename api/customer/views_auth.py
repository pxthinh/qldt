import json, time, hashlib
from datetime import datetime, timedelta, timezone as dt_timezone
from django.utils import timezone
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.core import signing
from .models import Customer, RevokedAuthToken

AUTH_SALT = "customer-auth-token"
AUTH_MAX_AGE = 60 * 60 * 24 * 7  # 7 ngày

def _json_body(request):
    try:
        return json.loads(request.body or "{}")
    except json.JSONDecodeError:
        return {}

def _issue_token(customer_id: int) -> str:
    return signing.dumps({"id": customer_id, "iat": int(time.time())}, salt=AUTH_SALT)
def _get_bearer_token(request) -> str | None:
    auth = request.META.get("HTTP_AUTHORIZATION", "")
    if not auth.lower().startswith("bearer "):
        return None
    return auth.split(" ", 1)[1].strip()

def _token_fingerprint(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()

def _customer_from_token(request):
    token = _get_bearer_token(request)
    if not token:
        return None, JsonResponse({"detail": "Missing Bearer token"}, status=401)

    fp = _token_fingerprint(token)
    if RevokedAuthToken.objects.filter(fingerprint=fp, expires_at__gt=timezone.now()).exists():
        return None, JsonResponse({"detail": "Token revoked"}, status=401)

    try:
        data = signing.loads(token, salt=AUTH_SALT, max_age=AUTH_MAX_AGE)
        obj = Customer.objects.get(pk=data.get("id"))
        return obj, None
    except signing.SignatureExpired:
        return None, JsonResponse({"detail": "Token expired"}, status=401)
    except (signing.BadSignature, Customer.DoesNotExist):
        return None, JsonResponse({"detail": "Invalid token"}, status=401)

@csrf_exempt
@require_http_methods(["POST"])
def customer_login(request):
    """
    Body JSON: {"user_name": "...", "password": "..."}
    Trả về: token + thông tin customer (không bao gồm password)
    """
    body = _json_body(request)
    user_name = (body.get("user_name") or "").strip()
    password  = (body.get("password") or "").strip()

    if not user_name or not password:
        return JsonResponse({"detail": "user_name and password are required"}, status=400)

    try:
        obj = Customer.objects.get(user_name__iexact=user_name)
    except Customer.DoesNotExist:
        return JsonResponse({"detail": "Invalid credentials"}, status=401)

    if not obj.check_password(password):
        return JsonResponse({"detail": "Invalid credentials"}, status=401)

    if hasattr(obj, "is_email_verified") and not obj.is_email_verified:
        return JsonResponse({"detail": "Email not verified"}, status=403)

    token = _issue_token(obj.pk)
    return JsonResponse({
        "token": token,
        "token_expires_in": AUTH_MAX_AGE,
        "customer": {
            "customer_id": obj.customer_id,
            "user_name": obj.user_name,
            "first_name": obj.first_name,
            "last_name": obj.last_name,
            "email": obj.email,
            "phone": obj.phone,
            "street": obj.street, "city": obj.city, "state": obj.state, "zip_code": obj.zip_code,
        }
    }, status=200)

@require_http_methods(["GET"])
def customer_me(request):
    obj, error = _customer_from_token(request)
    if error:
        return error
    return JsonResponse({
        "customer_id": obj.customer_id,
        "user_name": obj.user_name,
        "first_name": obj.first_name,
        "last_name": obj.last_name,
        "email": obj.email,
        "phone": obj.phone,
        "street": obj.street, "city": obj.city, "state": obj.state, "zip_code": obj.zip_code,
    })

@csrf_exempt
@require_http_methods(["POST"])
def customer_logout(request):
    """
    Thu hồi Bearer token hiện tại (đưa vào blacklist đến khi hết hạn).
    Header: Authorization: Bearer <token>
    """
    token = _get_bearer_token(request)
    if not token:
        return JsonResponse({"detail": "Missing Bearer token"}, status=401)

    expires_at = timezone.now() + timedelta(seconds=AUTH_MAX_AGE)

    try:
        data = signing.loads(token, salt=AUTH_SALT, max_age=AUTH_MAX_AGE)
        iat = data.get("iat")
        if isinstance(iat, int):
            issued_at = datetime.fromtimestamp(iat, tz=dt_timezone.utc)
            expires_at = issued_at + timedelta(seconds=AUTH_MAX_AGE)
    except signing.SignatureExpired:
        return JsonResponse({"detail": "Already expired"}, status=200)
    except signing.BadSignature:
        return JsonResponse({"detail": "Logged out"}, status=200)

    fp = _token_fingerprint(token)
    RevokedAuthToken.objects.get_or_create(
        fingerprint=fp,
        defaults={"expires_at": expires_at},
    )
    return JsonResponse({"detail": "Logged out"}, status=200)

