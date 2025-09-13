import json, time
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.core import signing
from django.urls import reverse
from .models import Customer

PWRESET_SALT = "customer-password-reset"
PWRESET_MAX_AGE = 60 * 60  # 1 giờ

def _json_body(request):
    try:
        return json.loads(request.body or "{}")
    except json.JSONDecodeError:
        return {}

def _build_reset_url(request, token: str) -> str:
    path = reverse("customer-password-reset-confirm")
    return request.build_absolute_uri(f"{path}?token={token}")

def _send_reset_email(request, customer: Customer):
    from django.core.mail import send_mail
    subject = "Đặt lại mật khẩu của bạn"
    token = signing.dumps({"id": customer.pk, "email": (customer.email or "").lower(), "ts": int(time.time())},
                          salt=PWRESET_SALT)
    url = _build_reset_url(request, token)
    message = (
        f"Chào {customer.first_name or customer.user_name},\n\n"
        f"Bạn đã yêu cầu đặt lại mật khẩu. Nhấn vào liên kết dưới đây để đặt mật khẩu mới "
        f"(hiệu lực trong 1 giờ):\n{url}\n\n"
        f"Nếu bạn không yêu cầu, hãy bỏ qua email này."
    )
    send_mail(subject, message, None, [customer.email], fail_silently=False)

@csrf_exempt
@require_http_methods(["POST"])
def password_reset_request(request):
    body = _json_body(request)
    user_name = (body.get("user_name") or "").strip()
    email = (body.get("email") or "").strip().lower()

    try:
        if user_name:
            obj = Customer.objects.get(user_name__iexact=user_name)
        elif email:
            obj = Customer.objects.get(email__iexact=email)
        else:
            return JsonResponse({"detail": "user_name hoặc email là bắt buộc"}, status=400)

        if obj.email:
            _send_reset_email(request, obj)
    except Customer.DoesNotExist:
        pass

    return JsonResponse({"detail": "Nếu tài khoản tồn tại, email đặt lại mật khẩu đã được gửi."})

@csrf_exempt
@require_http_methods(["POST"])
def password_reset_confirm(request):
    body = _json_body(request)

    token = body.get("token") or request.GET.get("token")
    new_password = (body.get("new_password") or "").strip()
    confirm_password = (body.get("confirm_password") or body.get("password_confirm") or "").strip()

    if not token:
        return JsonResponse({"detail": "token is required"}, status=400)
    if not new_password or len(new_password) < 6:
        return JsonResponse({"detail": "new_password tối thiểu 6 ký tự"}, status=400)
    if not confirm_password:
        return JsonResponse({"detail": "confirm_password is required"}, status=400)
    if new_password != confirm_password:
        return JsonResponse({"detail": "password confirmation does not match"}, status=400)

    try:
        data = signing.loads(token, salt=PWRESET_SALT, max_age=PWRESET_MAX_AGE)
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
