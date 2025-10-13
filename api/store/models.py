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
