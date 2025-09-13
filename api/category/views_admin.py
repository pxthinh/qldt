import json
from django.http import JsonResponse, HttpResponseNotAllowed
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils.timezone import now
from .models import Category

def _staff_required(view):
    return login_required(user_passes_test(lambda u: u.is_staff)(view))

def _json_body(request):
    try:
        return json.loads(request.body or "{}")
    except json.JSONDecodeError:
        return {}

# @_staff_required
@require_http_methods(["GET","POST"])
@csrf_exempt
def category_admin_list(request):
    if request.method == "GET":
        q = request.GET.get("name")
        qs = Category.objects.all()
        if q:
            qs = qs.filter(category_name__icontains=q)
        data = list(qs.order_by("-created_at").values(
            "category_id","category_name","created_at","updated_at"
        ))
        return JsonResponse(data, safe=False)

    # POST (create)
    body = _json_body(request)
    name = (body.get("category_name") or "").strip()
    if not name:
        return JsonResponse({"detail":"category_name is required"}, status=400)
    if Category.objects.filter(category_name__iexact=name).exists():
        return JsonResponse({"detail":"category_name already exists"}, status=400)
    obj = Category.objects.create(category_name=name, created_at=now(), updated_at=now())
    return JsonResponse({
        "category_id": obj.category_id,
        "category_name": obj.category_name,
        "created_at": obj.created_at, "updated_at": obj.updated_at
    }, status=201)

# @_staff_required
@require_http_methods(["GET","PUT","PATCH","DELETE"])
@csrf_exempt
def category_admin_detail(request, id: int):
    try:
        obj = Category.objects.get(pk=id)
    except Category.DoesNotExist:
        return JsonResponse({"detail":"Not found"}, status=404)

    if request.method == "GET":
        return JsonResponse({
            "category_id": obj.category_id, "category_name": obj.category_name,
            "created_at": obj.created_at, "updated_at": obj.updated_at
        })

    if request.method in ("PUT","PATCH"):
        body = _json_body(request)
        name = body.get("category_name")
        if name is not None:
            name = name.strip()
            if not name:
                return JsonResponse({"detail":"category_name cannot be empty"}, status=400)
            if Category.objects.exclude(pk=obj.pk)\
                    .filter(category_name__iexact=name).exists():
                return JsonResponse({"detail":"category_name already exists"}, status=400)
            obj.category_name = name
        obj.updated_at = now()
        obj.save()
        return JsonResponse({
            "category_id": obj.category_id, "category_name": obj.category_name,
            "created_at": obj.created_at, "updated_at": obj.updated_at
        })

    if request.method == "DELETE":
        obj.delete()
        return JsonResponse({"detail":"deleted"}, status=204)

    return HttpResponseNotAllowed(["GET","PUT","PATCH","DELETE"])
