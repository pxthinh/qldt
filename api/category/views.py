from django.http import JsonResponse
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from rest_framework.decorators import api_view
from repository.category_repository import list_categories

@swagger_auto_schema(
    method='get',
    tags=['FE'],
    operation_summary="Get all categories",
    operation_description="Retrieve a list of all categories",
    responses={
        200: openapi.Response('List of categories'),
    }
)
@api_view(['GET'])
def get_all(request):
    return JsonResponse(list_categories(request.GET), safe=False)
