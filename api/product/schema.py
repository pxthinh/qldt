from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status

# Query parameters for product list
product_name_query = openapi.Parameter(
    'name',
    openapi.IN_QUERY,
    description="Filter products by name (case-insensitive contains)",
    type=openapi.TYPE_STRING
)

brand_id_query = openapi.Parameter(
    'brand_id',
    openapi.IN_QUERY,
    description="Filter products by brand ID",
    type=openapi.TYPE_INTEGER
)

category_id_query = openapi.Parameter(
    'category_id',
    openapi.IN_QUERY,
    description="Filter products by category ID",
    type=openapi.TYPE_INTEGER
)

min_price_query = openapi.Parameter(
    'min_price',
    openapi.IN_QUERY,
    description="Filter products by minimum price",
    type=openapi.TYPE_NUMBER,
    format='decimal'
)

max_price_query = openapi.Parameter(
    'max_price',
    openapi.IN_QUERY,
    description="Filter products by maximum price",
    type=openapi.TYPE_NUMBER,
    format='decimal'
)

min_year_query = openapi.Parameter(
    'min_year',
    openapi.IN_QUERY,
    description="Filter products by minimum model year (inclusive)",
    type=openapi.TYPE_INTEGER,
    minimum=1900,
    maximum=2100
)

max_year_query = openapi.Parameter(
    'max_year',
    openapi.IN_QUERY,
    description="Filter products by maximum model year (inclusive)",
    type=openapi.TYPE_INTEGER,
    minimum=1900,
    maximum=2100
)

order_by_query = openapi.Parameter(
    'order_by',
    openapi.IN_QUERY,
    description="Field to order by (id, name, price, year)",
    type=openapi.TYPE_STRING,
    enum=['id', 'name', 'price', 'year'],
    default='id'
)

order_direction_query = openapi.Parameter(
    'order',
    openapi.IN_QUERY,
    description="Sort order (asc or desc)",
    type=openapi.TYPE_STRING,
    enum=['asc', 'desc'],
    default='desc'
)

# Stock item schema
stock_item_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    required=['store_id', 'quantity'],
    properties={
        'store_id': openapi.Schema(
            type=openapi.TYPE_INTEGER,
            description='ID of the store',
            example=1
        ),
        'quantity': openapi.Schema(
            type=openapi.TYPE_INTEGER,
            description='Quantity in stock',
            example=10,
            minimum=0
        )
    }
)

# Request body schema for creating/updating a product
product_request_body = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    required=['product_name', 'list_price', 'model_year'],
    properties={
        'product_name': openapi.Schema(
            type=openapi.TYPE_STRING,
            description='Name of the product',
            example='Classic T-Shirt',
            min_length=1,
            max_length=255
        ),
        'brand_id': openapi.Schema(
            type=openapi.TYPE_INTEGER,
            description='ID of the brand (optional)',
            example=1
        ),
        'category_id': openapi.Schema(
            type=openapi.TYPE_INTEGER,
            description='ID of the category (optional)',
            example=1
        ),
        'model_year': openapi.Schema(
            type=openapi.TYPE_INTEGER,
            description='Model year of the product (1900-2100)',
            example=2023,
            minimum=1900,
            maximum=2100
        ),
        'list_price': openapi.Schema(
            type=openapi.TYPE_NUMBER,
            description='Price of the product',
            example=99.99,
            minimum=0
        ),
        'stocks': openapi.Schema(
            type=openapi.TYPE_ARRAY,
            items=stock_item_schema,
            description='List of stock entries for different stores',
            example=[{"store_id": 1, "quantity": 10}]
        )
    },
    example={
        'product_name': 'Classic T-Shirt',
        'brand_id': 1,
        'category_id': 1,
        'model_year': 2023,
        'list_price': 99.99,
        'stocks': [
            {
                'store_id': 1,
                'quantity': 10
            }
        ]
    }
)

# Stock info schema for response
stock_info_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'total_stock': openapi.Schema(
            type=openapi.TYPE_INTEGER,
            description='Total quantity across all stores',
            example=10
        ),
        'stocks': openapi.Schema(
            type=openapi.TYPE_ARRAY,
            items=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'id': openapi.Schema(type=openapi.TYPE_INTEGER, example=1),
                    'store_id': openapi.Schema(type=openapi.TYPE_INTEGER, example=1),
                    'store_name': openapi.Schema(type=openapi.TYPE_STRING, example='Main Store'),
                    'quantity': openapi.Schema(type=openapi.TYPE_INTEGER, example=10),
                    'updated_at': openapi.Schema(type=openapi.TYPE_STRING, format='date-time')
                }
            )
        )
    }
)

# Response schema for a single product
product_response = openapi.Response(
    'Product details',
    schema=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'product_id': openapi.Schema(type=openapi.TYPE_INTEGER),
            'product_name': openapi.Schema(type=openapi.TYPE_STRING),
            'brand': openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'id': openapi.Schema(type=openapi.TYPE_INTEGER),
                    'name': openapi.Schema(type=openapi.TYPE_STRING)
                }
            ),
            'category': openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'id': openapi.Schema(type=openapi.TYPE_INTEGER),
                    'name': openapi.Schema(type=openapi.TYPE_STRING)
                }
            ),
            'model_year': openapi.Schema(type=openapi.TYPE_INTEGER),
            'list_price': openapi.Schema(type=openapi.TYPE_NUMBER, format='decimal'),
            'created_at': openapi.Schema(type=openapi.TYPE_STRING, format='date-time'),
            'updated_at': openapi.Schema(type=openapi.TYPE_STRING, format='date-time'),
            'stock_info': stock_info_schema
        }
    )
)

# Response schema for product list
product_list_response = openapi.Response(
    'List of products',
    schema=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'count': openapi.Schema(type=openapi.TYPE_INTEGER, description='Total number of items'),
            'next': openapi.Schema(type=openapi.TYPE_STRING, format='uri', nullable=True, description='URL to next page'),
            'previous': openapi.Schema(type=openapi.TYPE_STRING, format='uri', nullable=True, description='URL to previous page'),
            'results': openapi.Schema(
                type=openapi.TYPE_ARRAY,
                items=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'product_id': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'product_name': openapi.Schema(type=openapi.TYPE_STRING),
                        'brand_name': openapi.Schema(type=openapi.TYPE_STRING, nullable=True),
                        'category_name': openapi.Schema(type=openapi.TYPE_STRING, nullable=True),
                        'model_year': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'list_price': openapi.Schema(type=openapi.TYPE_NUMBER, format='decimal'),
                        'stock_info': openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                'total_stock': openapi.Schema(type=openapi.TYPE_INTEGER, example=10)
                            }
                        )
                    }
                )
            )
        }
    )
)

# Path parameter for product ID
product_id_param = openapi.Parameter(
    'id',
    openapi.IN_PATH,
    description="ID of the product",
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
product_list_get_schema = swagger_auto_schema(
    method='get',
    operation_id="product_list",
    manual_parameters=[
        product_name_query,
        brand_id_query,
        category_id_query,
        min_price_query,
        max_price_query,
        min_year_query,
        max_year_query,
        order_by_query,
        order_direction_query
    ],
    responses={
        status.HTTP_200_OK: product_list_response,
        **common_error_responses
    },
    security=[{"Bearer": []}],
    tags=['Admin Products'],
    operation_summary='List Products (Admin)',
    operation_description='''Returns a paginated list of all products with optional filtering and sorting.
    
    **Filtering Options:**
    - `name`: Filter by product name (case-insensitive contains)
    - `brand_id`: Filter by brand ID
    - `category_id`: Filter by category ID
    - `min_price`: Minimum price (inclusive)
    - `max_price`: Maximum price (inclusive)
    - `min_year`: Minimum model year (inclusive, 1900-2100)
    - `max_year`: Maximum model year (inclusive, 1900-2100)
    
    **Sorting Options:**
    - `order_by`: Field to sort by (id, name, price, year)
    - `order`: Sort direction (asc or desc, default: desc)
    '''
)

product_create_schema = swagger_auto_schema(
    method='post',
    operation_id="product_create",
    request_body=product_request_body,
    responses={
        status.HTTP_201_CREATED: product_response,
        **common_error_responses
    },
    security=[{"Bearer": []}],
    tags=['Admin Products'],
    operation_summary='Create Product (Admin)',
    operation_description='Create a new product.'
)

product_retrieve_schema = swagger_auto_schema(
    method='get',
    operation_id="product_retrieve",
    manual_parameters=[product_id_param],
    responses={
        status.HTTP_200_OK: product_response,
        **common_error_responses
    },
    security=[{"Bearer": []}],
    tags=['Admin Products'],
    operation_summary='Retrieve Product (Admin)',
    operation_description='Retrieve details of a specific product by ID.'
)

product_update_schema = swagger_auto_schema(
    methods=['put', 'patch'],
    operation_id="product_update",
    manual_parameters=[product_id_param],
    request_body=product_request_body,
    responses={
        status.HTTP_200_OK: product_response,
        **common_error_responses
    },
    security=[{"Bearer": []}],
    tags=['Admin Products'],
    operation_summary='Update Product (Admin)',
    operation_description='Update a product by ID.'
)

product_delete_schema = swagger_auto_schema(
    method='delete',
    operation_id="product_delete",
    manual_parameters=[product_id_param],
    responses={
        status.HTTP_204_NO_CONTENT: 'Product successfully deleted',
        **common_error_responses
    },
    security=[{"Bearer": []}],
    tags=['Admin Products'],
    operation_summary='Delete Product (Admin)',
    operation_description='Delete a product by ID.'
)
