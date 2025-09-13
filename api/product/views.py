from django.http import JsonResponse
from repository.product_repository import list_products

def get_all(request):
    data = list_products(request.GET)
    return JsonResponse(data, safe=False)
