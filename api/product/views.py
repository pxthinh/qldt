from django.http import JsonResponse
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from rest_framework.decorators import api_view
from repository.product_repository import list_products

@swagger_auto_schema(
    method='get',
    tags=['FE'],
    operation_summary="Get all products",
    operation_description="Retrieve a list of all products",
    responses={
        200: openapi.Response('List of products'),
    }
)
@api_view(['GET'])
def get_all(request):
    data = list_products(request.GET)
    return JsonResponse(data, safe=False)
