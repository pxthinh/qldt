from django.db.models import Count, Sum, Q, F
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from api.product.models import Product
from api.store.models import Stock  # Updated import path for Stock model
from api.brand.models import Brand
from api.category.models import Category
from api.order.models import Order
from ..core.decorators import staff_required
from ..customer.models import Customer
from ..staff.models import Staff


@swagger_auto_schema(
    method='get',
    operation_description="Get dashboard statistics including counts of products, brands, categories, etc.",
    responses={
        200: openapi.Response(
            description="Dashboard statistics",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'status': openapi.Schema(type=openapi.TYPE_STRING),
                    'data': openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            'products': openapi.Schema(
                                type=openapi.TYPE_OBJECT,
                                properties={
                                    'total': openapi.Schema(type=openapi.TYPE_INTEGER),
                                    'low_stock': openapi.Schema(type=openapi.TYPE_INTEGER)
                                }
                            ),
                            'inventory': openapi.Schema(
                                type=openapi.TYPE_OBJECT,
                                properties={
                                    'total_value': openapi.Schema(type=openapi.TYPE_NUMBER, format=openapi.FORMAT_FLOAT)
                                }
                            ),
                            'categories': openapi.Schema(type=openapi.TYPE_INTEGER),
                            'brands': openapi.Schema(type=openapi.TYPE_INTEGER),
                            'users': openapi.Schema(
                                type=openapi.TYPE_OBJECT,
                                properties={
                                    'total_customers': openapi.Schema(type=openapi.TYPE_INTEGER),
                                    'total_staff': openapi.Schema(type=openapi.TYPE_INTEGER)
                                }
                            ),
                            'orders': openapi.Schema(
                                type=openapi.TYPE_OBJECT,
                                properties={
                                    'recent_30_days': openapi.Schema(type=openapi.TYPE_INTEGER)
                                }
                            )
                        }
                    )
                }
            )
        ),
        500: 'Internal Server Error'
    },
    tags=['Static']
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
@staff_required()
def dashboard_statistics(request):
    """
    Get dashboard statistics including counts of products, brands, categories, etc.
    """
    try:
        # Product statistics
        total_products = Product.objects.filter(deleted_at__isnull=True).count()
        low_stock_products = Product.objects.filter(
            deleted_at__isnull=True,
            stocks__quantity__lt=10  # Using 'stocks' (plural) as per the model's related_name
        ).distinct().count()
        
        # Stock statistics
        from django.db.models import F
        total_stock_value = Stock.objects.annotate(
            stock_value=F('quantity') * F('product__list_price')
        ).aggregate(
            total_value=Sum('stock_value')
        )['total_value'] or 0
        
        # Category and brand counts
        total_categories = Category.objects.filter(deleted_at__isnull=True).count()
        total_brands = Brand.objects.filter(deleted_at__isnull=True).count()
        
        # User statistics
        total_customers = Customer.objects.count()  # All customers
        total_staff = Staff.objects.count()  # All staff members
        
        # Recent orders (last 30 days)
        thirty_days_ago = timezone.now() - timezone.timedelta(days=30)
        recent_orders = Order.objects.filter(
            created_at__gte=thirty_days_ago
        ).count()
        
        response_data = {
            'status': 'success',
            'data': {
                'products': {
                    'total': total_products,
                    'low_stock': low_stock_products,
                },
                'inventory': {
                    'total_value': float(total_stock_value) if total_stock_value else 0,
                },
                'categories': total_categories,
                'brands': total_brands,
                'users': {
                    'total_customers': total_customers,
                    'total_staff': total_staff,
                },
                'orders': {
                    'recent_30_days': recent_orders,
                }
            }
        }
        
        return Response(response_data)
        
    except Exception as e:
        return Response(
            {'status': 'error', 'message': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@swagger_auto_schema(
    method='get',
    operation_description="Get system health and status information",
    responses={
        200: openapi.Response(
            description="System health status",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'status': openapi.Schema(type=openapi.TYPE_STRING),
                    'data': openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            'database': openapi.Schema(type=openapi.TYPE_STRING),
                            'last_checked': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATETIME),
                            'counts': openapi.Schema(
                                type=openapi.TYPE_OBJECT,
                                properties={
                                    'products': openapi.Schema(type=openapi.TYPE_INTEGER),
                                    'categories': openapi.Schema(type=openapi.TYPE_INTEGER),
                                    'brands': openapi.Schema(type=openapi.TYPE_INTEGER)
                                }
                            ),
                            'version': openapi.Schema(type=openapi.TYPE_STRING),
                            'environment': openapi.Schema(type=openapi.TYPE_STRING)
                        }
                    )
                }
            )
        ),
        500: 'Internal Server Error'
    },
    tags=['Static']
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def system_health(request):
    """
    Get system health and status information
    """
    try:
        # Check database connectivity
        db_status = 'ok'
        try:
            Product.objects.first()  # Simple query to test DB connection
        except Exception:
            db_status = 'error'
        
        # Get counts for health check
        products_count = Product.objects.filter(deleted_at__isnull=True).count()
        categories_count = Category.objects.filter(deleted_at__isnull=True).count()
        brands_count = Brand.objects.filter(deleted_at__isnull=True).count()
        
        response_data = {
            'status': 'success',
            'data': {
                'database': db_status,
                'last_checked': timezone.now().isoformat(),
                'counts': {
                    'products': products_count,
                    'categories': categories_count,
                    'brands': brands_count,
                },
                'version': '1.0.0',  # You might want to get this from settings
                'environment': 'production'  # You might want to get this from settings
            }
        }
        
        return Response(response_data)
        
    except Exception as e:
        return Response(
            {'status': 'error', 'message': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
