from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status

# Query param dùng để lọc tên brand khi GET danh sách
brand_name_query = openapi.Parameter(
    'name',
    openapi.IN_QUERY,
    description="Filter brands by name (case-insensitive contains)",
    type=openapi.TYPE_STRING
)

# Request body schema cho POST tạo brand mới
brand_post_request_body = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    required=['brand_name'],
    properties={
        'brand_name': openapi.Schema(
            type=openapi.TYPE_STRING,
            description='Name of the brand',
            example='Chanel',
            min_length=1,
            max_length=100
        ),
    },
    example={'brand_name': 'Chanel'}
)

# Response schema cho danh sách brands
brand_list_response = openapi.Response(
    'List of brands',
    schema=openapi.Schema(
        type=openapi.TYPE_ARRAY,
        items=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'brand_id': openapi.Schema(type=openapi.TYPE_INTEGER),
                'brand_name': openapi.Schema(type=openapi.TYPE_STRING),
                'created_at': openapi.Schema(type=openapi.TYPE_STRING, format='date-time'),
                'updated_at': openapi.Schema(type=openapi.TYPE_STRING, format='date-time'),
            }
        )
    )
)

# Response schema cho chi tiết brand
brand_response = openapi.Response(
    'Brand details',
    schema=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'brand_id': openapi.Schema(type=openapi.TYPE_INTEGER),
            'brand_name': openapi.Schema(type=openapi.TYPE_STRING),
            'created_at': openapi.Schema(type=openapi.TYPE_STRING, format='date-time'),
            'updated_at': openapi.Schema(type=openapi.TYPE_STRING, format='date-time'),
        }
    )
)

# Path param cho ID brand
brand_id_param = openapi.Parameter(
    'id',
    openapi.IN_PATH,
    description="ID of the brand",
    type=openapi.TYPE_INTEGER
)

# Swagger decorator riêng cho GET method (list brands)
brand_list_get_schema = swagger_auto_schema(
    method='get',
    operation_id="brand_list",
    manual_parameters=[brand_name_query],
    responses={status.HTTP_200_OK: brand_list_response},
    security=[{"Bearer": []}],
    tags=['Brands'],
    operation_summary='List Brands',
    operation_description='Returns a list of all brands, optionally filtered by name.'
)

# Swagger decorator riêng cho POST method (create brand)
brand_list_post_schema = swagger_auto_schema(
    method='post',
    operation_id="brand_create",
    request_body=brand_post_request_body,
    responses={
        status.HTTP_201_CREATED: brand_response,
        status.HTTP_400_BAD_REQUEST: openapi.Response(
            "Bad Request",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "status": openapi.Schema(type=openapi.TYPE_STRING),
                    "message": openapi.Schema(type=openapi.TYPE_STRING),
                }
            )
        )
    },
    security=[{"Bearer": []}],
    tags=['Brands'],
    operation_summary='Create Brand',
    operation_description='Create a new brand by providing brand_name.'
)

# Swagger decorator cho detail: GET, PUT, PATCH, DELETE
brand_detail_schema = swagger_auto_schema(
    operation_description="Retrieve, update or delete a brand",
    manual_parameters=[brand_id_param],
    request_body=brand_post_request_body,
    responses={
        status.HTTP_200_OK: brand_response,
        status.HTTP_204_NO_CONTENT: 'Brand successfully deleted',
        status.HTTP_400_BAD_REQUEST: openapi.Response(
            description='Invalid input',
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "status": openapi.Schema(type=openapi.TYPE_STRING, example='error'),
                    "message": openapi.Schema(type=openapi.TYPE_STRING, example='Error message here'),
                }
            )
        ),
        status.HTTP_404_NOT_FOUND: 'Brand not found',
    },
    security=[{"Bearer": []}],
    tags=['Brands'],
)
