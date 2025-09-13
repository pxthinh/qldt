from django.http import JsonResponse
from repository.brand_repository import list_brands

def get_all(request):
    return JsonResponse(list_brands(request.GET), safe=False)
