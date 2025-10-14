from django.http import JsonResponse
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from repository.product_repository import list_products

@swagger_auto_schema(
    method='get',
    tags=['Products'],
    operation_summary="Get all products",
    operation_description="""
    Retrieve a paginated list of all available products with filtering and sorting options.
    
    ### Query Parameters:
    - `category`: Filter by category ID
    - `brand`: Filter by brand ID
    - `min_price`: Minimum price filter
    - `max_price`: Maximum price filter
    - `search`: Search in product name and description
    - `ordering`: Sort results by field (prefix with - for descending order)
    - `page`: Page number for pagination
    - `page_size`: Number of items per page
    """,
    manual_parameters=[
        openapi.Parameter('category', openapi.IN_QUERY, description="Filter by category ID", type=openapi.TYPE_INTEGER),
        openapi.Parameter('brand', openapi.IN_QUERY, description="Filter by brand ID", type=openapi.TYPE_INTEGER),
        openapi.Parameter('min_price', openapi.IN_QUERY, description="Minimum price", type=openapi.TYPE_NUMBER),
        openapi.Parameter('max_price', openapi.IN_QUERY, description="Maximum price", type=openapi.TYPE_NUMBER),
        openapi.Parameter('search', openapi.IN_QUERY, description="Search term", type=openapi.TYPE_STRING),
        openapi.Parameter('ordering', openapi.IN_QUERY, description="Sort by field (prefix with - for desc)", type=openapi.TYPE_STRING),
        openapi.Parameter('page', openapi.IN_QUERY, description="Page number", type=openapi.TYPE_INTEGER, default=1),
        openapi.Parameter('page_size', openapi.IN_QUERY, description="Items per page", type=openapi.TYPE_INTEGER, default=20),
    ],
    responses={
        200: openapi.Response(
            description="List of products",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'count': openapi.Schema(type=openapi.TYPE_INTEGER, description='Total number of items'),
                    'next': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FMT_URI, description='URL to next page', nullable=True),
                    'previous': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FMT_URI, description='URL to previous page', nullable=True),
                    'results': openapi.Schema(
                        type=openapi.TYPE_ARRAY,
                        items=openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                'id': openapi.Schema(type=openapi.TYPE_INTEGER, description='Product ID'),
                                'name': openapi.Schema(type=openapi.TYPE_STRING, description='Product name'),
                                'description': openapi.Schema(type=openapi.TYPE_STRING, description='Product description'),
                                'price': openapi.Schema(type=openapi.TYPE_NUMBER, format=openapi.FMT_DECIMAL, description='Product price'),
                                'image': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FMT_URI, description='Product image URL'),
                                'category': openapi.Schema(type=openapi.TYPE_STRING, description='Category name'),
                                'brand': openapi.Schema(type=openapi.TYPE_STRING, description='Brand name'),
                                'in_stock': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='Product availability'),
                                'rating': openapi.Schema(type=openapi.TYPE_NUMBER, format=openapi.FMT_DECIMAL, description='Average rating (0-5)')
                            }
                        )
                    )
                }
            )
        ),
        400: 'Bad Request - Invalid parameters',
        401: 'Unauthorized - Authentication required',
        403: 'Forbidden - Insufficient permissions',
        500: 'Internal Server Error'
    },
    security=[{"Bearer": []}]
)
@api_view(['GET'])
@permission_classes([AllowAny])
def get_all(request):
    data = list_products(request.GET)
    return JsonResponse(data, safe=False)
