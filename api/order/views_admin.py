from datetime import datetime, timedelta
from django.db import models
from django.db.models import F, Sum, DecimalField, Q, Count
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import viewsets, status, filters, permissions, serializers
from rest_framework.decorators import action
from rest_framework.parsers import JSONParser, MultiPartParser, FormParser
from rest_framework.response import Response

from .models import Order, OrderItem
from .serializers import OrderSerializer, OrderItemSerializer, OrderUpdateSerializer, OrderCreateSerializer

class OrderViewSet(viewsets.ModelViewSet):
    """
    Admin API endpoint for managing orders.
    
    This viewset provides the following actions:
    - list: Get a paginated list of all orders with filtering and search
    - create: Create a new order (admin only)
    - retrieve: Get details of a specific order
    - update: Update an existing order
    - partial_update: Partially update an order
    - destroy: Cancel/delete an order
    - status: Update order status
    - stats: Get order statistics
    - export: Export orders to CSV/Excel
    """
    schema = None  # Disable Swagger documentation for this viewset
    queryset = Order.objects.all().order_by('-order_date')
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAdminUser]
    parser_classes = [JSONParser, MultiPartParser, FormParser]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = [
        'order_id',
        'customer__email',
        'customer__first_name',
        'customer__last_name',
        'shipping_address__phone',
        'tracking_number'
    ]
    ordering_fields = [
        'order_date', 'required_date', 'shipped_date', 
        'order_status', 'total_amount', 'created_at'
    ]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Handle filtering by order_status
        order_status = self.request.query_params.get('order_status')
        if order_status:
            statuses = order_status.split(',')
            queryset = queryset.filter(order_status__in=statuses)
            
        # Handle date range filtering
        date_after = self.request.query_params.get('order_date_after')
        date_before = self.request.query_params.get('order_date_before')
        if date_after:
            queryset = queryset.filter(order_date__gte=date_after)
        if date_before:
            queryset = queryset.filter(order_date__lte=date_before)
            
        # Handle amount range filtering
        amount_min = self.request.query_params.get('total_amount_min')
        amount_max = self.request.query_params.get('total_amount_max')
        if amount_min:
            queryset = queryset.filter(total_amount__gte=float(amount_min))
        if amount_max:
            queryset = queryset.filter(total_amount__lte=float(amount_max))
            
        # Handle customer filter
        customer_id = self.request.query_params.get('customer')
        if customer_id:
            queryset = queryset.filter(customer_id=customer_id)
            
        return queryset
    
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