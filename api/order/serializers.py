from rest_framework import serializers
from .models import Order, OrderItem


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
        return obj.quantity * obj.list_price * (1 - obj.discount/100)


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
        read_only_fields = ['created_at', 'updated_at', 'total_amount']

    def create(self, validated_data):
        items_data = validated_data.pop('items', [])
        order = Order.objects.create(**validated_data)
        
        for item_data in items_data:
            OrderItem.objects.create(order=order, **item_data)
            
        return order

    def update(self, instance, validated_data):
        items_data = validated_data.pop('items', None)
        
        # Update order fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        instance.save()
        
        # Update or create order items if provided
        if items_data is not None:
            # Keep track of existing item_ids to handle deletions
            existing_item_ids = set(instance.items.values_list('item_id', flat=True))
            updated_item_ids = set()
            
            # Update or create items
            for item_data in items_data:
                item_id = item_data.get('item_id')
                if item_id in existing_item_ids:
                    OrderItem.objects.filter(order=instance, item_id=item_id).update(**item_data)
                else:
                    OrderItem.objects.create(order=instance, **item_data)
                updated_item_ids.add(item_id)
            
            # Delete items not included in the update
            instance.items.exclude(item_id__in=updated_item_ids).delete()
        
        return instance


class OrderCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating orders with nested order items."""
    items = OrderItemSerializer(many=True, required=True)

    class Meta:
        model = Order
        fields = [
            'order_status', 'required_date', 'shipped_date', 
            'store', 'staff', 'items'
        ]
        extra_kwargs = {
            'order_status': {'required': True},
            'store': {'required': True},
            'items': {'required': True, 'min_length': 1}
        }

    def validate_items(self, value):
        if not value:
            raise serializers.ValidationError("At least one order item is required.")
        return value

    def create(self, validated_data):
        items_data = validated_data.pop('items')
        order = Order.objects.create(**validated_data)
        
        # Create order items
        for item_data in items_data:
            OrderItem.objects.create(order=order, **item_data)
            
        return order


class OrderUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating orders."""
    class Meta:
        model = Order
        fields = [
            'order_status', 'required_date', 'shipped_date',
            'store', 'staff'
        ]
        extra_kwargs = {
            'order_status': {'required': False},
            'required_date': {'required': False},
            'shipped_date': {'required': False},
            'store': {'required': False},
            'staff': {'required': False}
        }

    def update(self, instance, validated_data):
        # Only update fields that are provided in the request
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        instance.save()
        return instance
