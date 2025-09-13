from django.http import JsonResponse
from repository.category_repository import list_categories

def get_all(request):
    return JsonResponse(list_categories(request.GET), safe=False)
