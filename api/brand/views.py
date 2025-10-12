from django.http import JsonResponse
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from rest_framework.decorators import api_view
from repository.brand_repository import list_brands

@swagger_auto_schema(
    method='get',
    tags=['FE'],
    operation_summary="Get all brands",
    operation_description="Retrieve a list of all brands",
    responses={
        200: openapi.Response('List of brands'),
    }
)
@api_view(['GET'])
def get_all(request):
    return JsonResponse(list_brands(request.GET), safe=False)
