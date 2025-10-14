from django.db import models
from django.contrib.auth.hashers import make_password, check_password
from django.utils import timezone
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager

class CustomerManager(BaseUserManager):
    def create_user(self, user_name, password=None, **extra_fields):
        if not user_name:
            raise ValueError('The Username must be set')
        user = self.model(user_name=user_name, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, user_name, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(user_name, password, **extra_fields)

class Customer(AbstractBaseUser, PermissionsMixin):
    objects = CustomerManager()
    
    USERNAME_FIELD = 'user_name'
    REQUIRED_FIELDS = []  # Add any required fields here
    
    @property
    def is_authenticated(self):
        """
        Always return True for authenticated users.
        This is a way to tell if the user has been authenticated in templates.
        """
        return True
        
    customer_id = models.AutoField(primary_key=True)

    user_name = models.CharField(max_length=150, unique=True, db_index=True)
    password  = models.CharField(max_length=128)

    first_name = models.CharField(max_length=50)
    last_name  = models.CharField(max_length=50, blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(max_length=254, blank=True, null=True)
    street = models.CharField(max_length=255, blank=True, null=True)
    city   = models.CharField(max_length=100, blank=True, null=True)
    state  = models.CharField(max_length=100, blank=True, null=True)
    zip_code = models.CharField(max_length=20, blank=True, null=True)

    is_email_verified = models.BooleanField(default=False)

    class Meta:
        indexes = [
            models.Index(fields=["user_name"]),
            models.Index(fields=["email"]),
            models.Index(fields=["phone"]),
        ]

    def __str__(self):
        return (f"{self.first_name} {self.last_name or ''}").strip()

    def set_password(self, raw_password: str):
        self.password = make_password(raw_password)

    def check_password(self, raw_password: str) -> bool:
        return check_password(raw_password, self.password)

    def save(self, *args, **kwargs):
        if self.password and "$" not in self.password:
            self.password = make_password(self.password)
        super().save(*args, **kwargs)

class RevokedAuthToken(models.Model):
    fingerprint = models.CharField(max_length=64, unique=True, db_index=True)
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["expires_at"]),
        ]

    def is_active(self) -> bool:
        return self.expires_at > timezone.now()