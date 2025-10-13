from django.db import models
from django.db.models import F, Sum
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.translation import gettext_lazy as _
from api.base.models import TimestampedModelWithManager
from api.store.models import Store, Stock

class Product(TimestampedModelWithManager):
    product_id = models.AutoField(primary_key=True)
    product_name = models.CharField(max_length=255, db_index=True)

    brand = models.ForeignKey(
        'brand.Brand',
        on_delete=models.PROTECT,
        db_column='brand_id',
        related_name='products',
        null=True, blank=True,
    )
    category = models.ForeignKey(
        'category.Category',
        on_delete=models.PROTECT,
        db_column='category_id',
        related_name='products',
        null=True, blank=True,
    )

    model_year = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1900), MaxValueValidator(2100)]
    )

    list_price = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )

    class Meta(TimestampedModelWithManager.Meta):
        verbose_name = "Product"
        verbose_name_plural = "Products"
        indexes = [
            models.Index(fields=["product_name"]),
            models.Index(fields=["brand_id"]),
            models.Index(fields=["category"]),
            models.Index(fields=["deleted_at"]),
        ]

    def __str__(self):
        return self.product_name
    
    def get_stock_quantity(self, store_id):
        """Get current stock quantity for a specific store"""
        try:
            stock = Stock.objects.get(store_id=store_id, product=self)
            return stock.quantity
        except Stock.DoesNotExist:
            return 0
    
    def get_total_stock(self):
        """Get total stock quantity across all stores"""
        return Stock.objects.filter(product=self).aggregate(
            total_stock=Sum('quantity')
        )['total_stock'] or 0
    
    def is_in_stock(self, store_id=None, quantity=1):
        """Check if product is in stock in the specified store (or any store if not specified)"""
        if store_id:
            return self.get_stock_quantity(store_id) >= quantity
        return self.get_total_stock() >= quantity
    
    def initialize_stock(self):
        """Initialize stock for this product in all stores"""
        stores = Store.objects.all()
        for store in stores:
            Stock.objects.get_or_create(
                store=store,
                product=self,
                defaults={'quantity': 0}
            )
    
    def update_stock(self, store_id, quantity_change):
        """Update stock quantity for this product in a specific store"""
        if not hasattr(self, '_stock_manager'):
            self._stock_manager = Stock.objects
        
        stock, created = self._stock_manager.get_or_create(
            store_id=store_id,
            product=self,
            defaults={'quantity': max(0, quantity_change)}
        )
        
        if not created:
            stock.quantity = F('quantity') + quantity_change
            stock.save(update_fields=['quantity', 'updated_at'])
        
        return stock


@receiver(post_save, sender=Product)
def create_product_stock(sender, instance, created, **kwargs):
    """Signal to create stock entries when a new product is created"""
    if created:
        instance.initialize_stock()
