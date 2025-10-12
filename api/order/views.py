from rest_framework import viewsets, status, filters, permissions, pagination
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.parsers import JSONParser, MultiPartParser, FormParser
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.db import transaction
from django.utils import timezone
from .models import Order, OrderItem
from .serializers import OrderSerializer, OrderItemSerializer, OrderCreateSerializer, OrderUpdateSerializer

class StandardResultsSetPagination(pagination.PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100
from .serializers import OrderSerializer, OrderItemSerializer, OrderCreateSerializer, OrderUpdateSerializer
from django.db import transaction

class IsCustomer(permissions.BasePermission):
    """
    Custom permission to only allow customers to access the view.
    """
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and hasattr(request.user, 'customer'))

@swagger_auto_schema(
    tags=['FE'],
    operation_description="Order management endpoints"
)
class OrderViewSet(viewsets.ModelViewSet):
    """
    A viewset for viewing and managing customer orders.
    Only accessible by customers, and they can only access their own orders.
    """
    queryset = Order.objects.all().order_by('-order_date')
    serializer_class = OrderSerializer
    permission_classes = [IsCustomer]  # Only allow customers
    pagination_class = StandardResultsSetPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['order_id', 'order_status']
    ordering_fields = ['order_date', 'required_date', 'shipped_date', 'order_status']
    parser_classes = [JSONParser, MultiPartParser, FormParser]
    
    def get_swagger_tags(self):
        return ['FE']
        
        if self.action == 'create':
            return OrderCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return OrderUpdateSerializer
        return OrderSerializer

    def get_queryset(self):
        """Return only the orders belonging to the current customer."""
        # Handle schema generation and unauthenticated users
        if getattr(self, 'swagger_fake_view', False) or not hasattr(self.request.user, 'customer'):
            return self.queryset.none()
        return self.queryset.filter(customer=self.request.user.customer)

    @swagger_auto_schema(
        operation_summary="List all orders",
        operation_description="""
        Get a paginated list of all orders for the current customer.
        Orders can be filtered and ordered by various fields.
        """,
        manual_parameters=[
            openapi.Parameter('search', openapi.IN_QUERY, 
                            description="Search by order ID or status", 
                            type=openapi.TYPE_STRING,
                            required=False),
            openapi.Parameter('ordering', openapi.IN_QUERY, 
                            description="Which field to use when ordering the results (prefix with '-' for descending order)", 
                            type=openapi.TYPE_STRING,
                            enum=['order_date', '-order_date', 'required_date', '-required_date', 
                                 'shipped_date', '-shipped_date', 'order_status', '-order_status'],
                            required=False),
            openapi.Parameter('status', openapi.IN_QUERY,
                            description="Filter by order status",
                            type=openapi.TYPE_STRING,
                            enum=['pending', 'processing', 'shipped', 'delivered', 'cancelled'],
                            required=False),
            openapi.Parameter('start_date', openapi.IN_QUERY,
                            description="Filter orders after this date (YYYY-MM-DD)",
                            type=openapi.TYPE_STRING,
                            format=openapi.FORMAT_DATE,
                            required=False),
            openapi.Parameter('end_date', openapi.IN_QUERY,
                            description="Filter orders before this date (YYYY-MM-DD)",
                            type=openapi.TYPE_STRING,
                            format=openapi.FORMAT_DATE,
                            required=False),
        ],
        responses={
            200: openapi.Response(
                description="List of orders",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'count': openapi.Schema(type=openapi.TYPE_INTEGER, description="Total number of items"),
                        'next': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_URI, description="URL to next page"),
                        'previous': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_URI, description="URL to previous page"),
                        'results': openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            items=openapi.Items(
                                type=openapi.TYPE_OBJECT,
                                properties={
                                    'id': openapi.Schema(type=openapi.TYPE_INTEGER),
                                    'order_id': openapi.Schema(type=openapi.TYPE_STRING),
                                    'order_date': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATETIME),
                                    'required_date': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATE, nullable=True),
                                    'shipped_date': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATE, nullable=True),
                                    'order_status': openapi.Schema(type=openapi.TYPE_STRING),
                                    'total_amount': openapi.Schema(type=openapi.TYPE_NUMBER, format=openapi.FORMAT_DECIMAL),
                                    'items_count': openapi.Schema(type=openapi.TYPE_INTEGER)
                                }
                            )
                        )
                    }
                )
            ),
            401: openapi.Response(
                description="Unauthorized",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'detail': openapi.Schema(type=openapi.TYPE_STRING)
                    }
                )
            ),
            403: openapi.Response(
                description="Forbidden",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'detail': openapi.Schema(type=openapi.TYPE_STRING)
                    }
                )
            )
        },
        security=[{"Bearer": []}]
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Create order",
        operation_description="""
        Create a new order with order items.
        
        Required fields:
        - shipping_address: Shipping address ID
        - payment_method: Payment method (e.g., 'credit_card', 'paypal')
        - items: Array of order items with product_id, quantity, and optional discount
        """,
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['shipping_address', 'payment_method', 'items'],
            properties={
                'shipping_address': openapi.Schema(type=openapi.TYPE_INTEGER, description='ID of the shipping address'),
                'payment_method': openapi.Schema(
                    type=openapi.TYPE_STRING, 
                    enum=['credit_card', 'paypal', 'bank_transfer'],
                    description='Payment method for the order'
                ),
                'notes': openapi.Schema(
                    type=openapi.TYPE_STRING, 
                    description='Additional notes for the order',
                    maxLength=500
                ),
                'items': openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        required=['product_id', 'quantity'],
                        properties={
                            'product_id': openapi.Schema(type=openapi.TYPE_INTEGER, description='ID of the product to order'),
                            'quantity': openapi.Schema(type=openapi.TYPE_INTEGER, minimum=1, description='Quantity to order'),
                            'discount': openapi.Schema(
                                type=openapi.TYPE_NUMBER, 
                                format=openapi.FORMAT_DECIMAL,
                                minimum=0,
                                maximum=1,
                                default=0,
                                description='Discount to apply (0-1)'
                            )
                        }
                    ),
                    minItems=1,
                    description='List of items to order'
                )
            }
        ),
        responses={
            201: openapi.Response(
                description="Order created successfully",
                schema=OrderSerializer(),
                examples={
                    "application/json": {
                        "id": 1,
                        "order_id": "ORD-20231011-12345",
                        "order_date": "2023-10-11T13:45:30Z",
                        "order_status": "pending",
                        "total_amount": "99.99",
                        "items_count": 2,
                        "shipping_address": {
                            "id": 1,
                            "address_line1": "123 Main St",
                            "city": "New York",
                            "state": "NY",
                            "postal_code": "10001",
                            "country": "US"
                        },
                        "items": [
                            {
                                "id": 1,
                                "product_id": 101,
                                "product_name": "Sample Product",
                                "quantity": 1,
                                "unit_price": "49.99",
                                "discount": "0.00",
                                "total_price": "49.99"
                            }
                        ]
                    }
                }
            ),
            400: openapi.Response(
                description="Bad Request",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'non_field_errors': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_STRING)),
                        'items': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_OBJECT)),
                        'shipping_address': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_STRING)),
                        'payment_method': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_STRING))
                    }
                ),
                examples={
                    "application/json": {
                        "items": [
                            {"product_id": ["This field is required."]},
                            {"quantity": ["This field is required."]}
                        ]
                    }
                }
            ),
            401: openapi.Response(
                description="Unauthorized",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'detail': openapi.Schema(type=openapi.TYPE_STRING)
                    }
                ),
                examples={
                    "application/json": {
                        "detail": "Authentication credentials were not provided."
                    }
                }
            ),
            403: openapi.Response(
                description="Forbidden",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'detail': openapi.Schema(type=openapi.TYPE_STRING)
                    }
                ),
                examples={
                    "application/json": {
                        "detail": "You do not have permission to perform this action."
                    }
                }
            ),
            404: openapi.Response(
                description="Not Found",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'detail': openapi.Schema(type=openapi.TYPE_STRING)
                    }
                ),
                examples={
                    "application/json": {
                        "detail": "Product with id=999 not found."
                    }
                }
            )
        },
        security=[{"Bearer": []}]
    )
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        with transaction.atomic():
            # Set the customer to the current user's customer profile
            order = serializer.save(customer=request.user.customer)
            
        headers = self.get_success_headers(serializer.data)
        return Response(
            OrderSerializer(order, context=self.get_serializer_context()).data,
            status=status.HTTP_201_CREATED,
            headers=headers
        )

    @swagger_auto_schema(
        operation_summary="Retrieve order",
        operation_description="Retrieve order details by ID",
        responses={
            200: openapi.Response('Order details', OrderSerializer()),
            401: openapi.Response('Unauthorized', schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={'detail': openapi.Schema(type=openapi.TYPE_STRING)}
            )),
            404: openapi.Response('Not Found', schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={'detail': openapi.Schema(type=openapi.TYPE_STRING)}
            ))
        }
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Update order",
        operation_description="Update an existing order (Customer only)",
        request_body=OrderUpdateSerializer,
        responses={
            200: openapi.Response('Order updated', OrderSerializer()),
            400: openapi.Response('Bad Request', schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={'detail': openapi.Schema(type=openapi.TYPE_STRING)}
            )),
            401: openapi.Response('Unauthorized', schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={'detail': openapi.Schema(type=openapi.TYPE_STRING)}
            )),
            403: openapi.Response('Forbidden', schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={'detail': openapi.Schema(type=openapi.TYPE_STRING)}
            )),
            404: openapi.Response('Not Found', schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={'detail': openapi.Schema(type=openapi.TYPE_STRING)}
            ))
        }
    )
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        
        # Only allow updating certain fields
        allowed_fields = ['shipping_address', 'billing_address', 'status']
        update_data = {k: v for k, v in request.data.items() if k in allowed_fields}
        
        serializer = self.get_serializer(instance, data=update_data, partial=partial)
        serializer.is_valid(raise_exception=True)
        
        with transaction.atomic():
            self.perform_update(serializer)
            
        return Response(OrderSerializer(instance).data)

    @swagger_auto_schema(
        operation_summary="Delete order",
        operation_description="Delete an order (only if status is 'pending'). Customer only.",
        responses={
            204: openapi.Response('No Content'),
            400: openapi.Response('Bad Request', schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={'detail': openapi.Schema(type=openapi.TYPE_STRING)}
            )),
            401: openapi.Response('Unauthorized', schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={'detail': openapi.Schema(type=openapi.TYPE_STRING)}
            )),
            403: openapi.Response('Forbidden', schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={'detail': openapi.Schema(type=openapi.TYPE_STRING)}
            )),
            404: openapi.Response('Not Found', schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={'detail': openapi.Schema(type=openapi.TYPE_STRING)}
            ))
        }
    )
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        
        # Only allow deletion of pending orders
        if instance.order_status != 'pending':
            return Response(
                {'detail': 'Only pending orders can be deleted'},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @swagger_auto_schema(
        method='get',
        operation_summary="List order items",
        operation_description="Get all items in a specific order",
        responses={
            200: openapi.Response('List of order items', OrderItemSerializer(many=True)),
            401: openapi.Response('Unauthorized', schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={'detail': openapi.Schema(type=openapi.TYPE_STRING)}
            )),
            404: openapi.Response('Not Found', schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={'detail': openapi.Schema(type=openapi.TYPE_STRING)}
            ))
        }
    )
    @action(detail=True, methods=['get'], url_path='items')
    def items(self, request, pk=None):
        """List all items in a specific order."""
        order = self.get_object()
        items = order.items.all()
        serializer = OrderItemSerializer(items, many=True, context=self.get_serializer_context())
        return Response(serializer.data)
