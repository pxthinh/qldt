from django.db import models
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone
from django.core.exceptions import ValidationError
from api.store.models import Stock

class Order(models.Model):
    """Order model for customer purchases."""
    class OrderStatus(models.IntegerChoices):
        PENDING = 1, 'Pending'
        PROCESSING = 2, 'Processing'
        SHIPPED = 3, 'Shipped'
        DELIVERED = 4, 'Delivered'
        CANCELLED = 5, 'Cancelled'

    order_id = models.AutoField(primary_key=True)
    customer = models.ForeignKey(
        'customer.Customer',
        on_delete=models.CASCADE,
        related_name='orders',
        null=True
    )
    order_status = models.PositiveSmallIntegerField(
        choices=OrderStatus.choices,
        default=OrderStatus.PENDING
    )
    order_date = models.DateField(default=timezone.now)
    required_date = models.DateField()
    shipped_date = models.DateField(null=True, blank=True)
    store = models.ForeignKey(
        'staff.Store',
        on_delete=models.CASCADE,
        related_name='orders'
    )
    staff = models.ForeignKey(
        'staff.Staff',
        on_delete=models.CASCADE,
        related_name='orders_handled'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Order {self.order_id} - {self.get_order_status_display()}"

    def save(self, *args, **kwargs):
        is_new = self._state.adding
        
        # Handle status changes for existing orders
        if not is_new:
            old_instance = Order.objects.get(pk=self.pk)
            if old_instance.order_status != self.order_status:
                self.handle_status_change(old_instance.order_status)
        
        super().save(*args, **kwargs)
    
    def handle_status_change(self, old_status):
        """Handle stock updates and validation when order status changes"""
        # Validate status transition
        valid_transitions = {
            self.OrderStatus.PENDING: [self.OrderStatus.PROCESSING, self.OrderStatus.CANCELLED],
            self.OrderStatus.PROCESSING: [self.OrderStatus.SHIPPED, self.OrderStatus.CANCELLED],
            self.OrderStatus.SHIPPED: [self.OrderStatus.DELIVERED],
            self.OrderStatus.DELIVERED: [],
            self.OrderStatus.CANCELLED: []
        }
        
        if (old_status != self.order_status and 
                self.order_status not in valid_transitions.get(old_status, [])):
            raise ValidationError(f"Invalid status transition from {self.get_order_status_display()} to {self.get_order_status_display()}")
        
        # Handle stock updates
        if (old_status == self.OrderStatus.PROCESSING and 
                self.order_status in [self.OrderStatus.SHIPPED, self.OrderStatus.CANCELLED]):
            # Reduce stock when shipping or cancelling a processing order
            for item in self.items.all():
                try:
                    Stock.update_stock(
                        store_id=self.store_id,
                        product_id=item.product_id,
                        quantity_change=-item.quantity if self.order_status == self.OrderStatus.SHIPPED else item.quantity
                    )
                except ValueError as e:
                    raise ValidationError(f"Stock update failed: {str(e)}")

    class Meta:
        db_table = 'orders'
        ordering = ['-order_date']


class OrderItem(models.Model):
    """Items within an order."""
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='items'
    )
    
    def clean(self):
        """Validate stock availability when order is being created or updated"""
        if self.order.order_status == Order.OrderStatus.PENDING and self.pk is None:
            try:
                stock = Stock.objects.get(
                    store_id=self.order.store_id,
                    product_id=self.product_id
                )
                if stock.quantity < self.quantity:
                    raise ValidationError({
                        'quantity': f'Insufficient stock. Only {stock.quantity} available.'
                    })
            except Stock.DoesNotExist:
                raise ValidationError({
                    'product': 'Product is not available in the selected store.'
                })
    item_id = models.PositiveSmallIntegerField()
    product = models.ForeignKey(
        'product.Product',
        on_delete=models.CASCADE,
        related_name='order_items'
    )
    quantity = models.IntegerField()
    list_price = models.DecimalField(max_digits=10, decimal_places=2)
    discount = models.DecimalField(max_digits=4, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'order_items'
        unique_together = (('order', 'item_id'),)
        ordering = ['order', 'item_id']

    def __str__(self):
        return f"{self.quantity}x {self.product.product_name} (Order {self.order_id})"

    @property
    def total_price(self):
        return self.quantity * self.list_price * (1 - self.discount)
