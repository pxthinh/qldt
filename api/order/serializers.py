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
        fields = ['customer', 'items']
        extra_kwargs = {
            'customer': {'required': True},
            'items': {'required': True, 'min_length': 1}
        }

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
        fields = ['order_status']
        extra_kwargs = {
            'order_status': {
                'required': False,
                'allow_null': False
            }
        }

    def update(self, instance, validated_data):
        # Only update fields that are provided in the request
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()
        return instance