from django.db import models
from ..base.models import TimestampedModelWithManager

class Category(TimestampedModelWithManager):
    category_id = models.AutoField(primary_key=True)
    category_name = models.CharField(max_length=50, unique=True, db_index=True)

    def __str__(self):
        return self.category_name

    class Meta(TimestampedModelWithManager.Meta):
        verbose_name_plural = "Categories"


