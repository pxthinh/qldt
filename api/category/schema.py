from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status

# Query parameters for category list
category_name_query = openapi.Parameter(
    'name',
    openapi.IN_QUERY,
    description="Filter categories by name (case-insensitive contains)",
    type=openapi.TYPE_STRING
)

# Sorting parameter for category list
sort_query = openapi.Parameter(
    'order',
    openapi.IN_QUERY,
    description="Sort order: 'newest' (default) or 'oldest'",
    type=openapi.TYPE_STRING,
    enum=['newest', 'oldest'],
    default='newest'
)

# Show deleted parameter
show_deleted_query = openapi.Parameter(
    'show_deleted',
    openapi.IN_QUERY,
    description="Set to 'true' to include soft-deleted categories",
    type=openapi.TYPE_BOOLEAN,
    default=False
)

# Request body schema for creating/updating a category
category_request_body = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    required=['category_name'],
    properties={
        'category_name': openapi.Schema(
            type=openapi.TYPE_STRING,
            description='Name of the category',
            example='Perfume',
            min_length=1,
            max_length=50
        ),
    },
    example={'category_name': 'Perfume'}
)

# Response schema for a single category
category_response = openapi.Response(
    'Category details',
    schema=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'category_id': openapi.Schema(type=openapi.TYPE_INTEGER, example=1),
            'category_name': openapi.Schema(type=openapi.TYPE_STRING, example='Electronics'),
            'created_at': openapi.Schema(type=openapi.TYPE_STRING, format='date-time'),
            'updated_at': openapi.Schema(type=openapi.TYPE_STRING, format='date-time')
        }
    )
)

# Response schema for category list
category_list_response = openapi.Response(
    'List of categories',
    schema=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'count': openapi.Schema(type=openapi.TYPE_INTEGER, description='Total number of items'),
            'next': openapi.Schema(type=openapi.TYPE_STRING, format='uri', nullable=True, description='URL to next page'),
            'previous': openapi.Schema(type=openapi.TYPE_STRING, format='uri', nullable=True, description='URL to previous page'),
            'sort': openapi.Schema(type=openapi.TYPE_STRING, description='Current sort order used'),
            'results': openapi.Schema(
                type=openapi.TYPE_ARRAY,
                items=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'category_id': openapi.Schema(type=openapi.TYPE_INTEGER, example=1),
                        'category_name': openapi.Schema(type=openapi.TYPE_STRING, example='Electronics'),
                        'created_at': openapi.Schema(type=openapi.TYPE_STRING, format='date-time'),
                        'updated_at': openapi.Schema(type=openapi.TYPE_STRING, format='date-time')
                    }
                )
            )
        }
    )
)

# Path parameter for category ID
category_id_param = openapi.Parameter(
    'id',
    openapi.IN_PATH,
    description="ID of the category",
    type=openapi.TYPE_INTEGER
)

# Error response schema
error_response = openapi.Response(
    "Error",
    schema=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'status': openapi.Schema(type=openapi.TYPE_STRING, example='error'),
            'message': openapi.Schema(type=openapi.TYPE_STRING, example='Error message here'),
            'errors': openapi.Schema(
                type=openapi.TYPE_OBJECT,
                additional_properties=openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(type=openapi.TYPE_STRING)
                )
            )
        }
    )
)

# Common error responses
common_error_responses = {
    status.HTTP_400_BAD_REQUEST: error_response,
    status.HTTP_401_UNAUTHORIZED: openapi.Response("Unauthorized"),
    status.HTTP_403_FORBIDDEN: openapi.Response("Forbidden"),
    status.HTTP_404_NOT_FOUND: openapi.Response("Not Found")
}

# Swagger decorators for different HTTP methods
category_list_get_schema = swagger_auto_schema(
    method='get',
    operation_id="category_list",
    manual_parameters=[
        category_name_query,
        sort_query,
        show_deleted_query
    ],
    responses={
        status.HTTP_200_OK: category_list_response,
        **common_error_responses
    },
    security=[{"Bearer": []}],
    tags=['Admin Categories'],
    operation_summary='List Categories (Admin)',
    operation_description='''Returns a paginated list of all categories.
    
    **Query Parameters:**
    - `name`: Filter categories by name (case-insensitive contains)
    - `order`: Sort order - 'newest' (default) or 'oldest'
    - `show_deleted`: Set to 'true' to include soft-deleted categories
    
    **Response includes:**
    - `sort`: Current sort order used
    - `count`: Total number of items
    - `next/previous`: Pagination URLs
    - `results`: List of categories
    '''
)

category_create_schema = swagger_auto_schema(
    method='post',
    operation_id="category_create",
    request_body=category_request_body,
    responses={
        status.HTTP_201_CREATED: category_response,
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
    tags=['Admin Categories'],
    operation_summary='Create Category (Admin)',
    operation_description='Create a new category.'
)

category_retrieve_schema = swagger_auto_schema(
    method='get',
    operation_id="category_retrieve",
    manual_parameters=[category_id_param],
    responses={
        status.HTTP_200_OK: category_response,
        **common_error_responses
    },
    security=[{"Bearer": []}],
    tags=['Admin Categories'],
    operation_summary='Retrieve Category (Admin)',
    operation_description='Retrieve details of a specific category by ID.'
)

category_update_schema = swagger_auto_schema(
    methods=['put', 'patch'],
    operation_id="category_update",
    manual_parameters=[category_id_param],
    request_body=category_request_body,
    responses={
        status.HTTP_200_OK: category_response,
        **common_error_responses
    },
    security=[{"Bearer": []}],
    tags=['Admin Categories'],
    operation_summary='Update Category (Admin)',
    operation_description='Update a category by ID.'
)

category_delete_schema = swagger_auto_schema(
    method='delete',
    operation_id="category_delete",
    manual_parameters=[category_id_param],
    responses={
        status.HTTP_204_NO_CONTENT: 'Category successfully deleted',
        **common_error_responses
    },
    security=[{"Bearer": []}],
    tags=['Admin Categories'],
    operation_summary='Delete Category (Admin)',
    operation_description='Delete a category by ID.'
)
