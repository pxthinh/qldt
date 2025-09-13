from django.shortcuts import render
from django.http.response import JsonResponse
from django.http import HttpResponse
from .models import Category;

def get_all(request):
    search_name = request.GET.get("name", None)

    data = Category.objects.all()

    if search_name:
        data = data.filter(category_name__icontains=search_name)

    data = data.order_by("-created_at").values(
        "category_id", "category_name", "created_at", "updated_at"
    )
    return JsonResponse(list(data.values()), safe=False)
