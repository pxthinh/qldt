from django.db import models
from django.contrib.auth.hashers import make_password, check_password
from django.conf import settings
from django.utils.crypto import get_random_string
from datetime import timedelta
from django.utils import timezone

# Import Store model using the full app path to avoid circular imports
from django.apps import apps

# This is a function to avoid circular imports
def get_store_model():
    return apps.get_model('store', 'Store')


class Store(models.Model):
    """Store model for managing retail locations."""
    store_id = models.AutoField(primary_key=True)
    store_name = models.CharField(max_length=255, db_index=True)
    phone = models.CharField(max_length=25, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    street = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=255, blank=True, null=True)
    state = models.CharField(max_length=10, blank=True, null=True)
    zip_code = models.CharField(max_length=5, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.store_name

    class Meta:
        db_table = 'stores'
        verbose_name = 'store'
        verbose_name_plural = 'stores'
        ordering = ['store_name']

class Staff(models.Model):
    """Staff member model."""
    staff_id = models.AutoField(primary_key=True)
    username = models.CharField(max_length=150, unique=True, db_index=True)
    email = models.EmailField(blank=True, null=True)
    first_name = models.CharField(max_length=50, blank=True)
    last_name = models.CharField(max_length=50, blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    password_hash = models.CharField(max_length=128, db_column='password', null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)
    
    # Store relationship
    store_id = models.IntegerField(null=True, blank=True)
    
    # Manager relationship
    manager = models.ForeignKey(
        'self',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='subordinates'
    )

    def __str__(self):
        return self.username or f"Staff {self.staff_id}"

    def set_password(self, raw_password: str) -> None:
        self.password_hash = make_password(raw_password)

    def check_password(self, raw_password: str) -> bool:
        return check_password(raw_password, self.password_hash)

    def save(self, *args, **kwargs):
        # Only hash password if it's set and not already hashed
        if hasattr(self, 'password') and not self.password_hash.startswith('pbkdf2_sha256$'):
            self.set_password(self.password)
        super().save(*args, **kwargs)

    class Meta:
        db_table = 'staff'
        verbose_name = 'staff member'
        verbose_name_plural = 'staff members'


class StaffToken(models.Model):
    """
    Custom token model for Staff authentication.
    """
    key = models.CharField(max_length=40, primary_key=True)
    staff = models.ForeignKey(
        Staff, 
        related_name='auth_tokens',
        on_delete=models.CASCADE,
        verbose_name="Staff"
    )
    created = models.DateTimeField(auto_now_add=True)
    expires = models.DateTimeField(null=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.key:
            self.key = self.generate_key()
        if not self.expires:
            self.expires = timezone.now() + timedelta(days=settings.TOKEN_EXPIRY_DAYS)
        return super().save(*args, **kwargs)

    def generate_key(self):
        return get_random_string(length=40)

    def is_expired(self):
        if not self.expires:
            return False
        return timezone.now() > self.expires

    def __str__(self):
        return f"Token for {self.staff.username} ({'expired' if self.is_expired() else 'active'})"

    class Meta:
        verbose_name = 'Staff Token'
        verbose_name_plural = 'Staff Tokens'
