import json
from typing import Mapping
from django.http import JsonResponse, HttpResponseNotAllowed
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Q
from .models import Customer

# ===== Helpers =====
def _staff_required(view):
    return login_required(user_passes_test(lambda u: u.is_staff)(view))

def _json_body(request):
    try:
        return json.loads(request.body or "{}")
    except json.JSONDecodeError:
        return {}

def _to_int(x, default=0, min_val=None, max_val=None):
    try:
        v = int(x)
    except Exception:
        v = default
    if min_val is not None and v < min_val: v = min_val
    if max_val is not None and v > max_val: v = max_val
    return v

_FIELD_MAP = {
    "id": "customer_id",
    "customer_id": "customer_id",
    "username": "user_name",
    "user_name": "user_name",
    "first_name": "first_name",
    "last_name": "last_name",
    "email": "email",
    "phone": "phone",
}

def _sanitize_update(body: Mapping[str, str]) -> dict:
    """Chỉ nhận những field được phép update (không cho client set id)."""
    allowed = [
        "user_name", "password",
        "first_name", "last_name",
        "phone", "email", "street", "city", "state", "zip_code",
    ]
    out = {}
    for k in allowed:
        if k in body:
            out[k] = body.get(k)
    return out

# ================== LIST + CREATE ==================
# @_staff_required               # bật khi cần bảo vệ bằng session admin
@require_http_methods(["GET", "POST"])
@csrf_exempt
def customer_admin_list(request):
    # -------- GET (list/search) --------
    if request.method == "GET":
        qs = Customer.objects.all()

        # search: q (username, name, email, phone)
        q = (request.GET.get("q") or "").strip()
        if q:
            qs = qs.filter(
                Q(user_name__icontains=q)
                | Q(first_name__icontains=q)
                | Q(last_name__icontains=q)
                | Q(email__icontains=q)
                | Q(phone__icontains=q)
            )

        # filter chi tiết
        username = (request.GET.get("username") or "").strip()
        if username:
            qs = qs.filter(user_name__icontains=username)

        email = (request.GET.get("email") or "").strip()
        if email:
            qs = qs.filter(email__icontains=email)

        phone = (request.GET.get("phone") or "").strip()
        if phone:
            qs = qs.filter(phone__icontains=phone)

        # ordering
        order_by_key = (request.GET.get("order_by") or "id").strip().lstrip("+").lower()
        direction = (request.GET.get("order") or "desc").strip().lower()  # asc|desc
        order_field = _FIELD_MAP.get(order_by_key, "customer_id")
        if direction == "desc":
            order_field = "-" + order_field
        qs = qs.order_by(order_field)

        # pagination (page/page_size ưu tiên; fallback offset/limit)
        page = request.GET.get("page")
        page_size = request.GET.get("page_size")
        if page or page_size:
            page = _to_int(page, default=1, min_val=1)
            page_size = _to_int(page_size, default=20, min_val=1, max_val=100)
            total = qs.count()
            offset = (page - 1) * page_size
            qs = qs[offset : offset + page_size]
        else:
            offset = _to_int(request.GET.get("offset"), default=0, min_val=0)
            limit = _to_int(request.GET.get("limit"), default=0, min_val=0, max_val=100)
            total = qs.count()
            if limit > 0:
                qs = qs[offset : offset + limit]
            page_size = limit if limit > 0 else total or 1
            page = (offset // page_size) + 1 if page_size else 1

        items = list(
            qs.values(
                "customer_id",
                "user_name",
                "first_name", "last_name",
                "email", "phone",
                "street", "city", "state", "zip_code",
            )
        )
        return JsonResponse({
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "order_by": order_by_key,
            "order": direction if direction in ("asc", "desc") else "desc",
        })

    body = _json_body(request)
    user_name = (body.get("user_name") or "").strip()
    password  = (body.get("password") or "").strip()
    first_name = (body.get("first_name") or "").strip()
    last_name  = body.get("last_name")
    email      = body.get("email")
    phone      = body.get("phone")
    street     = body.get("street")
    city       = body.get("city")
    state      = body.get("state")
    zip_code   = body.get("zip_code")

    if not user_name:
        return JsonResponse({"detail": "user_name is required"}, status=400)
    if not password:
        return JsonResponse({"detail": "password is required"}, status=400)
    if Customer.objects.filter(user_name__iexact=user_name).exists():
        return JsonResponse({"detail": "user_name already exists"}, status=400)
    if Customer.objects.filter(email__iexact=email).exists():
        return JsonResponse({"detail": "email already exists"}, status=400)

    obj = Customer(
        user_name=user_name,
        first_name=first_name,
        last_name=last_name,
        email=email,
        phone=phone,
        street=street, city=city, state=state, zip_code=zip_code,
    )
    obj.set_password(password)    # hash an toàn
    obj.save()

    return JsonResponse({
        "customer_id": obj.customer_id,
        "user_name": obj.user_name,
        "first_name": obj.first_name, "last_name": obj.last_name,
        "email": obj.email, "phone": obj.phone,
        "street": obj.street, "city": obj.city, "state": obj.state, "zip_code": obj.zip_code,
    }, status=201)

# @_staff_required
@require_http_methods(["GET", "PUT", "PATCH", "DELETE"])
@csrf_exempt
def customer_admin_detail(request, id: int):
    try:
        obj = Customer.objects.get(pk=id)
    except Customer.DoesNotExist:
        return JsonResponse({"detail": "Not found"}, status=404)

    # -------- GET (detail) --------
    if request.method == "GET":
        return JsonResponse({
            "customer_id": obj.customer_id,
            "user_name": obj.user_name,
            "first_name": obj.first_name, "last_name": obj.last_name,
            "email": obj.email, "phone": obj.phone,
            "street": obj.street, "city": obj.city, "state": obj.state, "zip_code": obj.zip_code,
        })

    if request.method in ("PUT", "PATCH"):
        body = _json_body(request)
        data = _sanitize_update(body)

        if "user_name" in data:
            new_username = (data["user_name"] or "").strip()
            if not new_username:
                return JsonResponse({"detail": "user_name cannot be empty"}, status=400)
            if Customer.objects.exclude(pk=obj.pk).filter(user_name__iexact=new_username).exists():
                return JsonResponse({"detail": "user_name already exists"}, status=400)
            obj.user_name = new_username

        if "password" in data:
            raw = (data["password"] or "").strip()
            if not raw:
                return JsonResponse({"detail": "password cannot be empty"}, status=400)
            if not obj.check_password(raw):
                obj.set_password(raw)

        for k in ["first_name", "last_name", "email", "phone", "street", "city", "state", "zip_code"]:
            if k in data:
                setattr(obj, k, data[k])

        obj.save()
        return JsonResponse({
            "customer_id": obj.customer_id,
            "user_name": obj.user_name,
            "first_name": obj.first_name, "last_name": obj.last_name,
            "email": obj.email, "phone": obj.phone,
            "street": obj.street, "city": obj.city, "state": obj.state, "zip_code": obj.zip_code,
        })

    if request.method == "DELETE":
        obj.delete()
        return JsonResponse({"detail": "deleted"}, status=204)

    return HttpResponseNotAllowed(["GET", "PUT", "PATCH", "DELETE"])
