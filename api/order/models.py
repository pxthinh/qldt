from django.db import models, transaction
from django.db.models import Sum, F, Q
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator
from api.store.models import Stock
from api.product.models import Product
from decimal import Decimal

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
            raise ValidationError(_(f"Invalid status transition from {self.get_order_status_display()} to {self.get_order_status_display()}"))
        
        # Handle stock updates
        with transaction.atomic():
            if (old_status == self.OrderStatus.PROCESSING and 
                    self.order_status in [self.OrderStatus.SHIPPED, self.OrderStatus.CANCELLED]):
                # Update stock based on status change
                for item in self.items.all():
                    try:
                        quantity_change = -item.quantity if self.order_status == self.OrderStatus.SHIPPED else item.quantity
                        Stock.update_stock(
                            store_id=self.store_id,
                            product_id=item.product_id,
                            quantity_change=quantity_change
                        )
                    except ValueError as e:
                        raise ValidationError(_(f"Stock update failed for product {item.product_id}: {str(e)}"))
            
            # Update order total when status changes to completed
            if self.order_status == self.OrderStatus.DELIVERED:
                self.update_order_total()
    
    def update_order_total(self):
        """Update the order total based on order items"""
        total = self.items.aggregate(
            total=Sum(F('quantity') * F('list_price') * (1 - F('discount') / 100))
        )['total'] or Decimal('0.00')
        self.total_amount = total
        self.save(update_fields=['total_amount', 'updated_at'])
    
    @property
    def can_be_cancelled(self):
        """Check if the order can be cancelled"""
        return self.order_status in [self.OrderStatus.PENDING, self.OrderStatus.PROCESSING]

    class Meta:
        db_table = 'orders'
        ordering = ['-order_date']


class OrderItem(models.Model):
    """Items within an order."""
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name=_('order')
    )
    product = models.ForeignKey(
        'store.Product',
        on_delete=models.PROTECT,
        related_name='order_items',
        verbose_name=_('product')
    )
    quantity = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1)],
        verbose_name=_('quantity')
    )
    list_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        verbose_name=_('list price')
    )
    discount = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name=_('discount %')
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'order_items'
        ordering = ['-created_at']
        verbose_name = _('order item')
        verbose_name_plural = _('order items')

    def __str__(self):
        return f"{self.quantity}x {self.product.product_name} (Order: {self.order_id})"
    
    def clean(self):
        """Validate order item before saving."""
        if not self.pk:  # Only for new items
            # Set list price from product if not provided
            if not self.list_price:
                self.list_price = self.product.price
            
            # Check stock availability
            if hasattr(self, 'order') and self.order.store_id:
                try:
                    stock = Stock.objects.get(
                        store=self.order.store,
                        product=self.product
                    )
                    if stock.quantity < self.quantity:
                        raise ValidationError({
                            'quantity': _(f'Insufficient stock. Available: {stock.quantity}')
                        })
                except Stock.DoesNotExist:
                    raise ValidationError({
                        'product': _('Product not available in the selected store')
                    })
    
    def save(self, *args, **kwargs):
        """Override save to include validation and update order total."""
        self.full_clean()
        super().save(*args, **kwargs)
        if hasattr(self, 'order'):
            self.order.update_order_total()
    
    @property
    def total_price(self):
        """Calculate total price for this order item."""
        return self.quantity * self.list_price * (1 - self.discount / 100)
    
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
