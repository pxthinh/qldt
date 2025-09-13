from django.http.response import JsonResponse
from .models import Brand

def get_all(request):
    search_name = request.GET.get("name")
    qs = Brand.objects.all()
    if search_name:
        qs = qs.filter(brand_name__icontains=search_name.strip())

    data = list(qs.order_by("-created_at").values(
        "brand_id", "brand_name", "created_at", "updated_at"
    ))
    return JsonResponse(data, safe=False)
