from rest_framework import status, filters
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.pagination import PageNumberPagination
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.http import JsonResponse
from repository.product_repository import list_products
from . import serializers

# Create serializer instance
ProductSerializer = serializers.ProductSerializer

class ProductListAPIView(APIView):
    """
    API endpoint that allows products to be viewed.
    """
    serializer_class = ProductSerializer
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['product_name', 'list_price', 'model_year']
    ordering = ['product_name']

    @swagger_auto_schema(
        tags=['FE'],
        operation_summary="Get all products",
        operation_description="""
        Retrieve a paginated list of products with advanced filtering and sorting options.
        
        ### Filtering:
        - `name`: Search in product name (case-insensitive)
        - `brand_id`: Filter by brand ID (comma-separated for multiple)
        - `category_id`: Filter by category ID (comma-separated for multiple)
        - `min_price`/`max_price`: Filter by price range
        - `min_year`/`max_year`: Filter by model year
        - `show_deleted`: Include deleted products (true/false)
        
        ### Pagination:
        - Use either:
          - `page` and `page_size` (1-based pagination)
          - `offset` and `limit` (0-based pagination)
        
        ### Sorting:
        - `order_by`: Field to sort by (id, name, price, year)
        - `order`: Sort direction (asc/desc, defaults to desc)
        """,
        manual_parameters=[
            openapi.Parameter('name', openapi.IN_QUERY, 
                            description="Search in product name", 
                            type=openapi.TYPE_STRING),
            openapi.Parameter('brand_id', openapi.IN_QUERY, 
                            description="Filter by brand ID(s), comma-separated", 
                            type=openapi.TYPE_STRING),
            openapi.Parameter('category_id', openapi.IN_QUERY, 
                            description="Filter by category ID(s), comma-separated", 
                            type=openapi.TYPE_STRING),
            openapi.Parameter('min_price', openapi.IN_QUERY, 
                            description="Minimum price", 
                            type=openapi.TYPE_NUMBER),
            openapi.Parameter('max_price', openapi.IN_QUERY, 
                            description="Maximum price", 
                            type=openapi.TYPE_NUMBER),
            openapi.Parameter('min_year', openapi.IN_QUERY, 
                            description="Minimum model year", 
                            type=openapi.TYPE_INTEGER),
            openapi.Parameter('max_year', openapi.IN_QUERY, 
                            description="Maximum model year", 
                            type=openapi.TYPE_INTEGER),
            openapi.Parameter('show_deleted', openapi.IN_QUERY, 
                            description="Include deleted products (true/false)", 
                            type=openapi.TYPE_BOOLEAN),
            openapi.Parameter('page', openapi.IN_QUERY, 
                            description="Page number (1-based)", 
                            type=openapi.TYPE_INTEGER),
            openapi.Parameter('page_size', openapi.IN_QUERY, 
                            description="Items per page (1-100)", 
                            type=openapi.TYPE_INTEGER),
            openapi.Parameter('offset', openapi.IN_QUERY, 
                            description="Offset for pagination (0-based)", 
                            type=openapi.TYPE_INTEGER),
            openapi.Parameter('limit', openapi.IN_QUERY, 
                            description="Maximum number of items to return (0-100)", 
                            type=openapi.TYPE_INTEGER),
            openapi.Parameter('order_by', openapi.IN_QUERY, 
                            description="Field to sort by (id, name, price, year)", 
                            type=openapi.TYPE_STRING,
                            default='id'),
            openapi.Parameter('order', openapi.IN_QUERY, 
                            description="Sort direction (asc/desc)", 
                            type=openapi.TYPE_STRING,
                            default='desc',
                            enum=['asc', 'desc']),
        ],
        responses={
            200: openapi.Response(
                description="List of products with pagination info",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'items': openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            items=openapi.Schema(
                                type=openapi.TYPE_OBJECT,
                                properties={
                                    'product_id': openapi.Schema(type=openapi.TYPE_INTEGER),
                                    'product_name': openapi.Schema(type=openapi.TYPE_STRING),
                                    'brand_id': openapi.Schema(type=openapi.TYPE_INTEGER, nullable=True),
                                    'brand_name': openapi.Schema(type=openapi.TYPE_STRING, nullable=True),
                                    'category_id': openapi.Schema(type=openapi.TYPE_INTEGER, nullable=True),
                                    'category_name': openapi.Schema(type=openapi.TYPE_STRING, nullable=True),
                                    'model_year': openapi.Schema(type=openapi.TYPE_INTEGER),
                                    'list_price': openapi.Schema(type=openapi.TYPE_NUMBER, format=openapi.FORMAT_DECIMAL),
                                    'total_stock': openapi.Schema(type=openapi.TYPE_INTEGER),
                                }
                            )
                        ),
                        'pagination': openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                'total': openapi.Schema(type=openapi.TYPE_INTEGER),
                                'page': openapi.Schema(type=openapi.TYPE_INTEGER),
                                'page_size': openapi.Schema(type=openapi.TYPE_INTEGER),
                                'total_pages': openapi.Schema(type=openapi.TYPE_INTEGER),
                                'has_next': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                                'has_prev': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                                'offset': openapi.Schema(type=openapi.TYPE_INTEGER),
                                'limit': openapi.Schema(type=openapi.TYPE_INTEGER),
                            }
                        ),
                        'ordering': openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                'order_by': openapi.Schema(type=openapi.TYPE_STRING),
                                'direction': openapi.Schema(type=openapi.TYPE_STRING, enum=['asc', 'desc'])
                            }
                        )
                    }
                )
            ),
            400: 'Bad Request - Invalid parameters',
        }
    )
    def get(self, request):
        data = list_products(request.GET)
        return JsonResponse(data, safe=False)
