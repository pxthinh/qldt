from django.db import transaction
from django.utils import timezone
from rest_framework import serializers
from .models import Order, OrderItem
from api.store.models import Stock


class OrderItemSerializer(serializers.ModelSerializer):
    """Serializer for OrderItem model."""
    total_price = serializers.SerializerMethodField()
    product_name = serializers.CharField(source='product.product_name', read_only=True)

    class Meta:
        model = OrderItem
        fields = [
            'item_id', 'product', 'product_name', 'quantity',
            'list_price', 'discount', 'total_price'
        ]
        extra_kwargs = {
            'product': {'write_only': True}
        }

    def get_total_price(self, obj):
        return obj.quantity * obj.list_price * (1 - obj.discount / 100)


class OrderSerializer(serializers.ModelSerializer):
    """Serializer for Order model with nested order items."""
    items = OrderItemSerializer(many=True, required=False)
    total_amount = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    customer_name = serializers.CharField(source='customer.get_full_name', read_only=True)
    staff_name = serializers.CharField(source='staff.get_full_name', read_only=True)
    store_name = serializers.CharField(source='store.store_name', read_only=True)
    order_status_display = serializers.CharField(
        source='get_order_status_display',
        read_only=True
    )

    class Meta:
        model = Order
        fields = [
            'order_id', 'customer', 'customer_name', 'order_status',
            'order_status_display', 'order_date', 'required_date',
            'shipped_date', 'store', 'store_name', 'staff', 'staff_name',
            'total_amount', 'created_at', 'updated_at', 'items'
        ]
        read_only_fields = [
            'created_at', 'updated_at', 'total_amount', 'order_date',
            'shipped_date'
        ]

    def create(self, validated_data):
        items_data = validated_data.pop('items', [])
        order = Order.objects.create(**validated_data)

        for item_data in items_data:
            OrderItem.objects.create(order=order, **item_data)

        return order


class OrderCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating orders with nested order items."""
    items = OrderItemSerializer(many=True, required=True)

    class Meta:
        model = Order
        fields = ['customer', 'items', 'store', 'staff']
        extra_kwargs = {
            'customer': {'required': True},
            'store': {'required': True},
            'staff': {'required': True},
            'items': {'required': True, 'min_length': 1}
        }

    def validate(self, attrs):
        items = attrs.get('items', [])
        store = attrs.get('store')
        
        # Validate stock availability for each item
        for item in items:
            product = item['product']
            quantity = item['quantity']
            
            try:
                stock = Stock.objects.get(store=store, product=product)
                if stock.quantity < quantity:
                    raise serializers.ValidationError(
                        f"Insufficient stock for {product.product_name}. "
                        f"Available: {stock.quantity}, Requested: {quantity}"
                    )
            except Stock.DoesNotExist:
                raise serializers.ValidationError(
                    f"Product {product.product_name} is not available in the selected store"
                )
        
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        items_data = validated_data.pop('items')
        
        # Set default status and order date
        validated_data['order_status'] = Order.OrderStatus.PENDING
        validated_data['order_date'] = timezone.now().date()
        
        # Create the order
        order = Order.objects.create(**validated_data)

        # Create order items and reduce stock
        for item_data in items_data:
            product = item_data['product']
            quantity = item_data['quantity']
            
            # Create order item
            OrderItem.objects.create(
                order=order,
                product=product,
                quantity=quantity,
                list_price=product.price,  # Store the price at time of order
                discount=product.discount or 0
            )
            
            # Reserve stock by reducing available quantity
            Stock.update_stock(
                store_id=order.store_id,
                product_id=product.id,
                quantity_change=-quantity
            )

        return order


class OrderUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating order status with validation."""
    status_display = serializers.CharField(source='get_order_status_display', read_only=True)

    class Meta:
        model = Order
        fields = ['order_status', 'status_display', 'shipped_date']
        read_only_fields = ['status_display', 'shipped_date']
        extra_kwargs = {
            'order_status': {
                'required': True,
                'allow_null': False
            }
        }

    def validate(self, attrs):
        instance = self.instance
        new_status = attrs.get('order_status')
        
        if not instance:
            return attrs
            
        current_status = instance.order_status
        
        # Don't allow updating cancelled or delivered orders
        if current_status in [Order.OrderStatus.CANCELLED, Order.OrderStatus.DELIVERED]:
            raise serializers.ValidationError(
                f"Cannot update an order that is {instance.get_order_status_display()}"
            )
            
        # Set shipped_date when status changes to SHIPPED
        if new_status == Order.OrderStatus.SHIPPED and current_status != Order.OrderStatus.SHIPPED:
            attrs['shipped_date'] = timezone.now().date()
            
        return attrs

    def update(self, instance, validated_data):
        new_status = validated_data.get('order_status')
        
        # Save the instance with new status
        instance.order_status = new_status
        
        # Let the model handle the status change logic
        instance.save(update_fields=['order_status', 'shipped_date'] if 'shipped_date' in validated_data else ['order_status'])
        
        return instance
        return instance