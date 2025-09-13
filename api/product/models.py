from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator

class Product(models.Model):
    product_id   = models.AutoField(primary_key=True)
    product_name = models.CharField(max_length=255)

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
        max_digits=10, decimal_places=2,
        validators=[MinValueValidator(0)]
    )

    class Meta:
        verbose_name = "Product"
        verbose_name_plural = "Products"
        indexes = [
            models.Index(fields=["product_name"]),
            models.Index(fields=["brand_id"]),
            models.Index(fields=["category"]),
        ]

    def __str__(self):
        return self.product_name
