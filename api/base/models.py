from django.db import models


class ActiveManager(models.Manager):
    """Manager to return only non-deleted objects."""
    def get_queryset(self):
        return super().get_queryset().filter(deleted_at__isnull=True)


class TimestampedModel(models.Model):
    """
    An abstract base class model that provides self-updating
    `created_at` and `updated_at` fields, and soft delete with `deleted_at`.
    """
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True, db_index=True)
    deleted_at = models.DateTimeField(blank=True, null=True, db_index=True)

    class Meta:
        abstract = True
        ordering = ['-created_at']

    def delete(self, using=None, keep_parents=False):
        """Override delete to perform a soft delete."""
        from django.utils import timezone
        self.deleted_at = timezone.now()
        self.save(using=using, update_fields=['deleted_at'])

    def hard_delete(self, using=None, keep_parents=False):
        """Perform a hard delete."""
        return super().delete(using=using, keep_parents=keep_parents)


class TimestampedModelWithManager(TimestampedModel):
    """
    A concrete model that includes the ActiveManager.
    Other models should inherit from this instead of TimestampedModel directly.
    """
    objects = models.Manager()
    active_objects = ActiveManager()

    class Meta(TimestampedModel.Meta):
        abstract = True
