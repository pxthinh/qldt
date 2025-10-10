from django.db import models
from ..base.models import TimestampedModelWithManager

class Brand(TimestampedModelWithManager):
    brand_id = models.AutoField(primary_key=True)
    brand_name = models.CharField(max_length=80, unique=True, db_index=True)

    def __str__(self):
        return self.brand_name

    class Meta(TimestampedModelWithManager.Meta):
        db_table = "brands"
        verbose_name_plural = "Brands"