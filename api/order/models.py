from django.db import models
from django.utils import timezone

class Order(models.Model):
    """Order model for customer purchases."""
    class OrderStatus(models.IntegerChoices):
        PENDING = 1, 'Pending'
        PROCESSING = 2, 'Processing'
        REJECTED = 3, 'Rejected'
        COMPLETED = 4, 'Completed'

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
