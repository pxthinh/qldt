from decimal import Decimal
from django.db import transaction
from django.utils import timezone
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from django.db.models import F
from .models import Order, OrderItem
from api.store.models import Stock
from api.product.models import Product
from api.product.serializers import ProductSerializer


class OrderItemCreateSerializer(serializers.ModelSerializer):
    product_id = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.all(),
        source='product',
        write_only=True
    )

    class Meta:
        model = OrderItem
        fields = ['product_id', 'quantity', 'list_price', 'discount']
        extra_kwargs = {
            'quantity': {'required': True, 'min_value': 1},
            'list_price': {'required': False},
            'discount': {'required': False, 'min_value': 0, 'max_value': 100}
        }

    def validate(self, attrs):
        if 'list_price' not in attrs:
            attrs['list_price'] = attrs['product'].list_price
        return attrs


class OrderItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    total_price = serializers.SerializerMethodField()

    class Meta:
        model = OrderItem
        fields = ['id', 'product', 'quantity', 'list_price', 'discount', 'total_price', 'created_at']
        read_only_fields = ['id', 'created_at', 'total_price']

    def get_total_price(self, obj):
        return obj.quantity * obj.list_price * (1 - obj.discount / 100)


class OrderCreateSerializer(serializers.ModelSerializer):
    customer = serializers.IntegerField(required=False, write_only=True)
    store = serializers.IntegerField(required=True, write_only=True)
    shipping_address = serializers.CharField(required=True, write_only=True)
    payment_method = serializers.CharField(required=True, write_only=True)
    items = OrderItemCreateSerializer(many=True, required=True, write_only=True)

    class Meta:
        model = Order
        fields = ['customer', 'store', 'shipping_address', 'payment_method', 'items']


    def validate(self, attrs):
        request = self.context.get('request', None)

        # Handle customer
        customer_id = attrs.pop('customer', None)
        if customer_id is not None:
            from api.customer.models import Customer
            try:
                attrs['customer'] = Customer.objects.get(pk=customer_id)
            except Customer.DoesNotExist:
                raise serializers.ValidationError({"customer": ["Customer not found."]})
        elif request and hasattr(request.user, 'customer'):
            attrs['customer'] = request.user.customer

        # Handle store
        store_id = attrs.pop('store', None)
        if store_id is not None:
            from api.store.models import Store
            try:
                attrs['store'] = Store.objects.get(pk=store_id)
            except Store.DoesNotExist:
                raise serializers.ValidationError({"store": ["Store not found."]})

        # Set staff from request user if available
        if request and hasattr(request.user, 'staff'):
            attrs['staff'] = request.user.staff

        # Set default values
        attrs['order_status'] = Order.OrderStatus.PENDING
        attrs['order_date'] = timezone.now().date()

        # Validate items and stock
        items_data = attrs.pop('items', [])
        if not items_data:
            raise serializers.ValidationError({"items": ["At least one item is required."]})

        for idx, item in enumerate(items_data):
            product = item.get('product')
            quantity = item.get('quantity')
            if product is None:
                raise serializers.ValidationError({f"items.{idx}.product_id": ["Product is required."]})
            if quantity < 1:
                raise serializers.ValidationError({f"items.{idx}.quantity": ["Quantity must be at least 1."]})
            try:
                stock = Stock.objects.get(store=attrs['store'], product=product)
                if stock.quantity < quantity:
                    raise serializers.ValidationError({
                        f"items.{idx}.quantity": [f"Insufficient stock. Available: {stock.quantity}"]
                    })
            except Stock.DoesNotExist:
                raise serializers.ValidationError({
                    f"items.{idx}.product": ["Product is not available in the selected store."]
                })
        attrs['validated_items'] = items_data
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        items_data = validated_data.pop('validated_items', [])
        shipping_address = validated_data.pop('shipping_address')
        payment_method = validated_data.pop('payment_method')

        order = Order.objects.create(
            **validated_data,
            shipping_address=shipping_address,
            payment_method=payment_method
        )

        order_items = []
        for item in items_data:
            # Reduce stock atomically
            Stock.objects.filter(
                product=item['product'],
                store=order.store
            ).update(quantity=F('quantity') - item['quantity'])

            order_items.append(OrderItem(
                order=order,
                product=item['product'],
                quantity=item['quantity'],
                list_price=item.get('list_price', item['product'].list_price),
                discount=item.get('discount', 0),
            ))
        OrderItem.objects.bulk_create(order_items)
        order.update_order_total()
        return order


class OrderUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ['order_status', 'shipped_date']
        read_only_fields = ['shipped_date']

    def validate_order_status(self, value):
        instance = self.instance
        valid_transitions = {
            Order.OrderStatus.PENDING: [Order.OrderStatus.PROCESSING, Order.OrderStatus.CANCELLED],
            Order.OrderStatus.PROCESSING: [Order.OrderStatus.SHIPPED, Order.OrderStatus.CANCELLED],
            Order.OrderStatus.SHIPPED: [Order.OrderStatus.DELIVERED],
        }
        if value not in valid_transitions.get(instance.order_status, []):
            raise ValidationError(
                f"Invalid status transition from {instance.get_order_status_display()} to {value}"
            )
        if value == Order.OrderStatus.SHIPPED and not instance.shipped_date:
            self.validated_data['shipped_date'] = timezone.now().date()
        return value

    def update(self, instance, validated_data):
        instance.order_status = validated_data.get('order_status', instance.order_status)
        if 'shipped_date' in validated_data:
            instance.shipped_date = validated_data['shipped_date']
        instance.save()
        return instance


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    customer_name = serializers.CharField(source='customer.get_full_name', read_only=True)
    staff_name = serializers.CharField(source='staff.get_full_name', read_only=True, allow_null=True)
    store_name = serializers.CharField(source='store.store_name', read_only=True)
    order_status_display = serializers.CharField(source='get_order_status_display', read_only=True)

    class Meta:
        model = Order
        fields = [
            'order_id', 'order_date', 'required_date', 'shipped_date',
            'order_status', 'order_status_display',
            'customer_id', 'customer_name', 'staff_id', 'staff_name',
            'store_id', 'store_name', 'created_at', 'updated_at',
            'items'
        ]
        read_only_fields = [
            'order_date', 'created_at', 'updated_at',
            'order_status_display', 'customer_name', 'staff_name', 'store_name'
        ]
