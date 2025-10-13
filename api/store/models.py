from django.db import models
from django.utils.translation import gettext_lazy as _


class Store(models.Model):
    """
    Store model representing physical store locations.
    """
    store_name = models.CharField(
        _('store name'),
        max_length=255,
        help_text=_('The name of the store')
    )
    phone = models.CharField(
        _('phone number'),
        max_length=25,
        blank=True,
        null=True,
        help_text=_('Contact phone number for the store')
    )
    email = models.EmailField(
        _('email address'),
        max_length=255,
        blank=True,
        null=True,
        help_text=_('Contact email for the store')
    )
    street = models.CharField(
        _('street address'),
        max_length=255,
        blank=True,
        null=True,
        help_text=_('Street address of the store')
    )
    city = models.CharField(
        _('city'),
        max_length=255,
        blank=True,
        null=True,
        help_text=_('City where the store is located')
    )
    state = models.CharField(
        _('state'),
        max_length=10,
        blank=True,
        null=True,
        help_text=_('State/Province/Region code')
    )
    zip_code = models.CharField(
        _('zip code'),
        max_length=5,
        blank=True,
        null=True,
        help_text=_('Postal/ZIP code of the store location')
    )
    created_at = models.DateTimeField(
        _('created at'),
        auto_now_add=True,
        help_text=_('When the store record was created')
    )
    updated_at = models.DateTimeField(
        _('updated at'),
        auto_now=True,
        help_text=_('When the store record was last updated')
    )

    class Meta:
        db_table = 'sales.stores'
        verbose_name = _('store')
        verbose_name_plural = _('stores')
        ordering = ['store_name']

    def __str__(self):
        return self.store_name


class Stock(models.Model):
    """
    Tracks inventory levels for products in each store.
    """
    store = models.ForeignKey(
        Store,
        on_delete=models.CASCADE,
        related_name='stocks',
        help_text=_('The store where this stock is located')
    )
    product = models.ForeignKey(
        'product.Product',
        on_delete=models.CASCADE,
        related_name='stocks',
        help_text=_('The product in stock')
    )
    quantity = models.IntegerField(
        _('quantity'),
        default=0,
        help_text=_('Current quantity in stock')
    )
    created_at = models.DateTimeField(
        _('created at'),
        auto_now_add=True,
        help_text=_('When the stock record was created')
    )
    updated_at = models.DateTimeField(
        _('updated at'),
        auto_now=True,
        help_text=_('When the stock record was last updated')
    )

    class Meta:
        db_table = 'inventory.stocks'
        verbose_name = _('stock')
        verbose_name_plural = _('stocks')
        unique_together = ('store', 'product')

    def __str__(self):
        return f"{self.product.product_name} at {self.store.store_name}: {self.quantity}"
    
    @classmethod
    def update_stock(cls, store_id, product_id, quantity_change):
        """
        Update stock quantity for a product in a store.
        Use negative quantity_change to decrease stock.
        """
        stock, created = cls.objects.get_or_create(
            store_id=store_id,
            product_id=product_id,
            defaults={'quantity': 0}
        )
        stock.quantity += quantity_change
        if stock.quantity < 0:
            raise ValueError("Insufficient stock")
        stock.save()
        return stock
