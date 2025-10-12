from django.http import JsonResponse, HttpResponseNotAllowed
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils.timezone import now
from rest_framework.decorators import api_view, parser_classes, action
from rest_framework.viewsets import ViewSet
from rest_framework.parsers import JSONParser, FormParser, MultiPartParser
from rest_framework import status
from rest_framework.response import Response
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema

from .models import Order, OrderItem
from .serializers import OrderSerializer
from .schema import (
    order_status_query, date_after_query, date_before_query,
    order_create_request, order_update_request,
    order_detail_response, order_list_response, order_id_param
)


def _staff_required(view):
    return login_required(user_passes_test(lambda u: u.is_staff)(view))

class OrderAdminViewSet(ViewSet):
    """
    ViewSet for handling Order operations in the admin interface.
    """
    
    @swagger_auto_schema(
        operation_id="order_list",
        manual_parameters=[order_status_query, date_after_query, date_before_query],
        responses={
            status.HTTP_200_OK: order_list_response,
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
        tags=['Admin Orders'],
        operation_summary='List Orders (Admin)',
        operation_description='Returns a list of all orders, optionally filtered by status and date range.'
    )
    def list(self, request):
        """
        List all orders with optional filtering.
        """
        qs = Order.objects.all()
        
        # Apply filters
        status_filter = request.query_params.get('status')
        if status_filter:
            statuses = [s.strip().lower() for s in status_filter.split(',')]
            qs = qs.filter(status__in=statuses)
            
        date_after = request.query_params.get('date_after')
        if date_after:
            qs = qs.filter(created_at__gte=date_after)
            
        date_before = request.query_params.get('date_before')
        if date_before:
            qs = qs.filter(created_at__lte=date_before)
        
        serializer = OrderSerializer(qs.order_by("-created_at"), many=True)
        return Response(serializer.data)
    
    @swagger_auto_schema(
        operation_id="order_create",
        request_body=order_create_request,
        responses={
            status.HTTP_201_CREATED: order_detail_response,
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
        tags=['Admin Orders'],
        operation_summary='Create Order (Admin)',
        operation_description='Create a new order with the provided data.'
    )
    def create(self, request):
        """
        Create a new order.
        """
        try:
            data = request.data
            if hasattr(data, 'dict'):  # Handle QueryDict from form data
                data = data.dict()
                
            serializer = OrderSerializer(data=data)
            if serializer.is_valid():
                order = serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)
                
            return Response({
                "status": "error",
                "message": "Validation error",
                "errors": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            return Response({
                "status": "error",
                "message": f"Failed to create order: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        if request.method == 'GET':
            # GET method - List all orders
            qs = Order.objects.all()
            
            # Apply filters
            status_filter = request.query_params.get('status')
            if status_filter:
                statuses = [s.strip().lower() for s in status_filter.split(',')]
                qs = qs.filter(status__in=statuses)
                
            date_after = request.query_params.get('date_after')
            if date_after:
                qs = qs.filter(created_at__gte=date_after)
                
            date_before = request.query_params.get('date_before')
            if date_before:
                qs = qs.filter(created_at__lte=date_before)
            
            serializer = OrderSerializer(qs.order_by("-created_at"), many=True)
            return Response(serializer.data)
        
        elif request.method == 'POST':
            # POST method - Create a new order
            try:
                data = request.data
                if hasattr(data, 'dict'):  # Handle QueryDict from form data
                    data = data.dict()
                    
                serializer = OrderSerializer(data=data)
                if serializer.is_valid():
                    order = serializer.save()
                    return Response(serializer.data, status=status.HTTP_201_CREATED)
                    
                return Response({
                    "status": "error",
                    "message": "Validation error",
                    "errors": serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
                
            except Exception as e:
                return Response({
                    "status": "error",
                    "message": f"Failed to create order: {str(e)}"
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @swagger_auto_schema(
        operation_id="order_retrieve",
        responses={
            status.HTTP_200_OK: order_detail_response,
            status.HTTP_404_NOT_FOUND: 'Order not found'
        },
        security=[{"Bearer": []}],
        tags=['Admin Orders'],
        operation_summary='Retrieve Order (Admin)',
        operation_description='Retrieve details of a specific order by ID.'
    )
    def retrieve(self, request, pk=None):
        """
        Retrieve a specific order by ID.
        """
        try:
            order = Order.objects.get(pk=pk)
            serializer = OrderSerializer(order)
            return Response(serializer.data)
        except Order.DoesNotExist:
            return Response({"detail": "Not found"}, status=404)

    @swagger_auto_schema(
        operation_id="order_update",
        request_body=order_update_request,
        responses={
            status.HTTP_200_OK: order_detail_response,
            status.HTTP_400_BAD_REQUEST: 'Invalid input',
            status.HTTP_404_NOT_FOUND: 'Order not found',
        },
        security=[{"Bearer": []}],
        tags=['Admin Orders'],
        operation_summary='Update Order (Admin)',
        operation_description='Update an order by ID.'
    )
    def update(self, request, pk=None):
        """
        Update an order by ID.
        """
        try:
            order = Order.objects.get(pk=pk)
            data = request.data
            if hasattr(data, 'dict'):  # Handle QueryDict from form data
                data = data.dict()
                
            serializer = OrderSerializer(order, data=data, partial=False)
            if serializer.is_valid():
                updated_order = serializer.save()
                return Response(OrderSerializer(updated_order).data)
                
            return Response({
                "status": "error",
                "message": "Validation error",
                "errors": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
            
        except Order.DoesNotExist:
            return Response({"detail": "Not found"}, status=404)
        except Exception as e:
            return Response({
                "status": "error",
                "message": f"Failed to update order: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @swagger_auto_schema(
        operation_id="order_partial_update",
        request_body=order_update_request,
        responses={
            status.HTTP_200_OK: order_detail_response,
            status.HTTP_400_BAD_REQUEST: 'Invalid input',
            status.HTTP_404_NOT_FOUND: 'Order not found',
        },
        security=[{"Bearer": []}],
        tags=['Admin Orders'],
        operation_summary='Partially Update Order (Admin)',
        operation_description='Partially update an order by ID.'
    )
    def partial_update(self, request, pk=None):
        """
        Partially update an order by ID.
        """
        try:
            order = Order.objects.get(pk=pk)
            data = request.data
            if hasattr(data, 'dict'):  # Handle QueryDict from form data
                data = data.dict()
                
            serializer = OrderSerializer(order, data=data, partial=True)
            if serializer.is_valid():
                updated_order = serializer.save()
                return Response(OrderSerializer(updated_order).data)
                
            return Response({
                "status": "error",
                "message": "Validation error",
                "errors": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
            
        except Order.DoesNotExist:
            return Response({"detail": "Not found"}, status=404)
        except Exception as e:
            return Response({
                "status": "error",
                "message": f"Failed to update order: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @swagger_auto_schema(
        operation_id="order_delete",
        responses={
            status.HTTP_204_NO_CONTENT: 'Order successfully deleted',
            status.HTTP_404_NOT_FOUND: 'Order not found',
        },
        security=[{"Bearer": []}],
        tags=['Admin Orders'],
        operation_summary='Delete Order (Admin)',
        operation_description='Delete an order by ID.'
    )
    def destroy(self, request, pk=None):
        """
        Delete an order by ID.
        """
        try:
            order = Order.objects.get(pk=pk)
            order.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Order.DoesNotExist:
            return Response({"detail": "Not found"}, status=404)
        except Exception as e:
            return Response({
                "status": "error",
                "message": f"Failed to delete order: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def get_serializer_class(self):
        if self.action == 'items' and self.request.method == 'POST':
            return OrderItemSerializer
        if self.action == 'item_detail' and self.request.method in ['PUT', 'PATCH']:
            return OrderItemSerializer
        if self.action in ['update', 'partial_update']:
            return OrderUpdateSerializer
        if self.action == 'create':
            return OrderCreateSerializer
        return OrderSerializer
        
    def get_serializer_context(self):
        context = super().get_serializer_context()
        if self.action in ['update', 'partial_update', 'destroy']:
            context['order'] = self.get_object()
        return context

    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)
    
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)
    
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)
    
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)
    
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)
    
    @action(detail=True, methods=['get', 'post'])
    def items(self, request, pk=None):
        """
        Handle order items for a specific order.
        GET: List all items in the order
        POST: Add a new item to the order
        """
        order = self.get_object()
        
        if request.method == 'GET':
            items = order.items.all()
            serializer = OrderItemSerializer(items, many=True, context={'request': request})
            return Response(serializer.data)
            
        elif request.method == 'POST':
            data = request.data.copy()
            data['order'] = order.order_id
            
            # Auto-calculate item_id if not provided
            if 'item_id' not in data:
                last_item = order.items.order_by('-item_id').first()
                data['item_id'] = last_item.item_id + 1 if last_item else 1
            
            serializer = self.get_serializer(data=data)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['get', 'put', 'delete'], url_path=r'items/(?P<item_id>[0-9]+)')
    def item_detail(self, request, pk=None, item_id=None):
        """
        Handle a specific order item.
        GET: Get item details
        PUT: Update item
        DELETE: Remove item from order
        """
        order = self.get_object()
        try:
            item = order.items.get(item_id=item_id)
        except OrderItem.DoesNotExist:
            return Response(
                {'error': 'Item not found in this order'},
                status=status.HTTP_404_NOT_FOUND
            )
            
        if request.method == 'GET':
            serializer = OrderItemSerializer(item)
            return Response(serializer.data)
            
        elif request.method == 'PUT':
            serializer = OrderItemSerializer(item, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
        elif request.method == 'DELETE':
            item.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
    
    @action(detail=True, methods=['post'])
    def status(self, request, pk=None):
        """
        Update order status with optional tracking number and notes.
        """
        order = self.get_object()
        new_status = request.data.get('status')
        tracking_number = request.data.get('tracking_number')
        notes = request.data.get('notes')
        
        if not new_status:
            return Response(
                {'error': 'Status is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        # Update order status and other fields
        order.order_status = new_status
        if tracking_number is not None:
            order.tracking_number = tracking_number
        if notes is not None:
            order.notes = notes
            
        order.save()
        
        return Response(OrderSerializer(order).data)
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        # Parse timeframe parameter (default to last 30 days)
        timeframe = request.query_params.get('timeframe', '30d')
        
        try:
            # Convert timeframe to days
            if timeframe.endswith('d'):
                days = int(timeframe[:-1])
            elif timeframe.endswith('w'):
                days = int(timeframe[:-1]) * 7
            elif timeframe.endswith('m'):
                days = int(timeframe[:-1]) * 30
            elif timeframe.endswith('y'):
                days = int(timeframe[:-1]) * 365
            else:
                days = int(timeframe) if timeframe.isdigit() else 30
        except (ValueError, TypeError):
            days = 30
            
        start_date = timezone.now() - timedelta(days=days)
        
        # Get base queryset
        queryset = self.filter_queryset(self.get_queryset())
        recent_orders = queryset.filter(order_date__gte=start_date)
        
        # Calculate statistics
        stats = {
            'total_orders': recent_orders.count(),
            'total_revenue': float(recent_orders.aggregate(total=Sum('total_amount'))['total'] or 0),
            'orders_by_status': dict(recent_orders.values_list('order_status').annotate(
                count=Count('id')
            )),
            'recent_orders': list(recent_orders.select_related('customer').order_by('-order_date')[:5].values(
                'id', 'order_id', 'total_amount', 'order_date', 'order_status',
                customer_name=models.F('customer__first_name') + ' ' + models.F('customer__last_name')
            )),
            'top_customers': list(recent_orders.values(
                'customer_id',
                'customer__first_name',
                'customer__last_name'
            ).annotate(
                order_count=Count('id'),
                total_spent=Sum('total_amount')
            ).order_by('-total_spent')[:5]),
            'timeframe': f"last_{days}_days"
        }
        
        # Calculate average order value
        stats['avg_order_value'] = (
            stats['total_revenue'] / stats['total_orders'] 
            if stats['total_orders'] > 0 else 0
        )
        
        return Response(stats)
    @action(detail=True, methods=['get', 'post'])
    def items(self, request, pk=None):
        """
        Handle order items for a specific order.
        GET: List all items in the order
        POST: Add a new item to the order
        """
        order = self.get_object()
        
        if request.method == 'GET':
            items = order.items.all()
            serializer = OrderItemSerializer(items, many=True, context={'request': request})
            return Response(serializer.data)
            
        elif request.method == 'POST':
            data = request.data.copy()
            data['order'] = order.order_id
            
            # Auto-calculate item_id if not provided
            if 'item_id' not in data:
                last_item = order.items.order_by('-item_id').first()
                data['item_id'] = (last_item.item_id + 1) if last_item else 1
                
            serializer = OrderItemSerializer(data=data, context={'request': request})
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['get', 'put', 'delete'], url_path='items/(?P<item_id>[0-9]+)')
    def item_detail(self, request, pk=None, item_id=None):
        """
        Handle a specific order item.
        GET: Get item details
        PUT: Update item
        DELETE: Remove item from order
        """
        order = self.get_object()
        try:
            item = order.items.get(item_id=item_id)
        except OrderItem.DoesNotExist:
            return Response(
                {'error': 'Item not found in this order'},
                status=status.HTTP_404_NOT_FOUND
            )
            
        if request.method == 'GET':
            serializer = OrderItemSerializer(item, context={'request': request})
            return Response(serializer.data)
            
        elif request.method == 'PUT':
            serializer = OrderItemSerializer(item, data=request.data, partial=True, context={'request': request})
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
        elif request.method == 'DELETE':
            item.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
            
        if request.method == 'GET':
            serializer = OrderItemSerializer(item)
            return Response(serializer.data)
            
        elif request.method == 'PUT':
            serializer = OrderItemSerializer(item, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
        elif request.method == 'DELETE':
            item.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)