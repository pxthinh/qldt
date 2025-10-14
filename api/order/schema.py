from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status

# Query parameters
order_status_query = openapi.Parameter(
    'status',
    openapi.IN_QUERY,
    description="Filter orders by status (comma-separated values)",
    type=openapi.TYPE_STRING
)

date_after_query = openapi.Parameter(
    'date_after',
    openapi.IN_QUERY,
    description="Filter orders created after this date (YYYY-MM-DD)",
    type=openapi.TYPE_STRING,
    format=openapi.FORMAT_DATE
)

date_before_query = openapi.Parameter(
    'date_before',
    openapi.IN_QUERY,
    description="Filter orders created before this date (YYYY-MM-DD)",
    type=openapi.TYPE_STRING,
    format=openapi.FORMAT_DATE
)

# Request body schemas
order_create_request = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    required=['customer_id', 'items'],
    properties={
        'customer_id': openapi.Schema(
            type=openapi.TYPE_INTEGER,
            description="ID of the customer placing the order",
            example=1
        ),
        'shipping_address': openapi.Schema(
            type=openapi.TYPE_STRING,
            description="Full shipping address for the order",
            example="123 Main St, City, Country, 10001"
        ),
        'payment_method': openapi.Schema(
            type=openapi.TYPE_STRING,
            description="Payment method for the order",
            enum=["credit_card", "paypal", "bank_transfer", "cod"],
            example="credit_card"
        ),
        'store': openapi.Schema(
            type=openapi.TYPE_INTEGER,
            description="ID of the store placing the order",
            example=1
        ),
        'items': openapi.Schema(
            type=openapi.TYPE_ARRAY,
            description="List of order items",
            minItems=1,
            items=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                required=['product_id', 'quantity'],
                properties={
                    'product_id': openapi.Schema(
                        type=openapi.TYPE_INTEGER,
                        description="ID of the product being ordered",
                        example=101
                    ),
                    'quantity': openapi.Schema(
                        type=openapi.TYPE_INTEGER,
                        description="Quantity of the product",
                        minimum=1,
                        example=2
                    )
                }
            )
        )
    },
    example={
        "customer_id": 1,
        "store": 2,
        "shipping_address": "123 Main St, City, Country, 10001",
        "payment_method": "credit_card",
        "items": [
            {
                "product_id": 5,
                "quantity": 2
            },
            {
                "product_id": 7,
                "quantity": 1
            }
        ]
    }
)

order_update_request = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    description="Update order details",
    properties={
        'status': openapi.Schema(
            type=openapi.TYPE_STRING,
            description="Updated status of the order",
            enum=['pending', 'processing', 'shipped', 'delivered', 'cancelled'],
            example="shipped"
        ),
        'shipping_tracking': openapi.Schema(
            type=openapi.TYPE_STRING,
            description="Tracking number for the shipment",
            example="1Z999AA1234567890",
            maxLength=50
        ),
        'shipping_address': openapi.Schema(
            type=openapi.TYPE_STRING,
            description="Updated shipping address (if changed)",
            example="456 New St, City, Country, 20001"
        ),
        'payment_status': openapi.Schema(
            type=openapi.TYPE_STRING,
            description="Updated payment status",
            enum=['pending', 'paid', 'refunded', 'failed'],
            example="paid"
        ),
        'notes': openapi.Schema(
            type=openapi.TYPE_STRING,
            description="Additional notes or comments about the order update",
            example="Customer requested signature confirmation"
        ),
        'cancellation_reason': openapi.Schema(
            type=openapi.TYPE_STRING,
            description="Required if status is set to 'cancelled'",
            example="Out of stock"
        )
    },
    example={
        "status": "shipped",
        "shipping_tracking": "1Z999AA1234567890",
        "notes": "Shipped via UPS Ground",
        "payment_status": "paid"
    }
)

# Response schemas
order_item_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'id': openapi.Schema(type=openapi.TYPE_INTEGER),
        'product': openapi.Schema(type=openapi.TYPE_OBJECT, properties={
            'id': openapi.Schema(type=openapi.TYPE_INTEGER),
            'name': openapi.Schema(type=openapi.TYPE_STRING)
        }),
        'quantity': openapi.Schema(type=openapi.TYPE_INTEGER),
        'unit_price': openapi.Schema(type=openapi.TYPE_NUMBER, format=openapi.FORMAT_DECIMAL),
        'total_price': openapi.Schema(type=openapi.TYPE_NUMBER, format=openapi.FORMAT_DECIMAL)
    }
)

order_detail_response = openapi.Response(
    'Order details',
    schema=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'id': openapi.Schema(type=openapi.TYPE_INTEGER),
            'order_number': openapi.Schema(type=openapi.TYPE_STRING),
            'customer': openapi.Schema(type=openapi.TYPE_OBJECT, properties={
                'id': openapi.Schema(type=openapi.TYPE_INTEGER),
                'email': openapi.Schema(type=openapi.TYPE_STRING)
            }),
            'status': openapi.Schema(type=openapi.TYPE_STRING),
            'total_amount': openapi.Schema(type=openapi.TYPE_NUMBER, format=openapi.FORMAT_DECIMAL),
            'created_at': openapi.Schema(type=openapi.TYPE_STRING, format='date-time'),
            'updated_at': openapi.Schema(type=openapi.TYPE_STRING, format='date-time'),
            'items': openapi.Schema(type=openapi.TYPE_ARRAY, items=order_item_schema)
        }
    )
)

order_list_response = openapi.Response(
    'List of orders',
    schema=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'count': openapi.Schema(type=openapi.TYPE_INTEGER),
            'next': openapi.Schema(type=openapi.TYPE_STRING, format='uri', nullable=True),
            'previous': openapi.Schema(type=openapi.TYPE_STRING, format='uri', nullable=True),
            'results': openapi.Schema(
                type=openapi.TYPE_ARRAY,
                items=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'id': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'order_number': openapi.Schema(type=openapi.TYPE_STRING),
                        'customer': openapi.Schema(type=openapi.TYPE_OBJECT, properties={
                            'id': openapi.Schema(type=openapi.TYPE_INTEGER),
                            'email': openapi.Schema(type=openapi.TYPE_STRING)
                        }),
                        'status': openapi.Schema(type=openapi.TYPE_STRING),
                        'total_amount': openapi.Schema(type=openapi.TYPE_NUMBER, format=openapi.FORMAT_DECIMAL),
                        'created_at': openapi.Schema(type=openapi.TYPE_STRING, format='date-time')
                    }
                )
            )
        }
    )
)

error_response = openapi.Response(
    'Error Response',
    schema=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'status': openapi.Schema(type=openapi.TYPE_STRING),
            'message': openapi.Schema(type=openapi.TYPE_STRING),
            'errors': openapi.Schema(type=openapi.TYPE_OBJECT)
        }
    )
)

# Common parameters
order_id_param = openapi.Parameter(
    'id',
    openapi.IN_PATH,
    description="Order ID",
    type=openapi.TYPE_INTEGER,
    required=True
)
