from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.contrib.auth.hashers import make_password
from django.utils.translation import gettext_lazy as _

class StaffManager(BaseUserManager):
    """Custom manager for the Staff model."""
    def create_user(self, username, email=None, password=None, **extra_fields):
        if not username:
            raise ValueError(_('The Username must be set'))
        email = self.normalize_email(email) if email else None
        
        # Create the user with the given fields
        user = self.model(
            username=username,
            email=email,
            **extra_fields
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, email=None, password=None, **extra_fields):
        # Set default values for superuser
        extra_fields.setdefault('is_active', True)
        
        # Create the user first
        user = self.create_user(
            username=username,
            email=email,
            password=password,
            **extra_fields
        )
        
        # Set superuser and staff status
        user.is_superuser = True
        user.is_staff = True
        user.save(using=self._db)
        return user

class Staff(AbstractBaseUser, PermissionsMixin):
    """Custom user model for staff members."""
    staff_id = models.AutoField(primary_key=True)
    username = models.CharField(_('username'), max_length=150, unique=True, db_index=True)
    email = models.EmailField(_('email address'), blank=True, null=True)
    first_name = models.CharField(_('first name'), max_length=50, blank=True)
    last_name = models.CharField(_('last name'), max_length=50, blank=True, null=True)
    phone = models.CharField(_('phone number'), max_length=20, blank=True, null=True)
    
    # Required fields
    is_active = models.BooleanField(_('active'), default=True)
    is_staff = models.BooleanField(_('staff status'), default=False)
    date_joined = models.DateTimeField(_('date joined'), auto_now_add=True)
    
    # Store and manager relationships
    store = models.IntegerField(_('store'), null=True, blank=True, db_column="store_id")
    manager = models.ForeignKey(
        'self',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        db_column='manager_id',
        related_name='subordinates',
        verbose_name=_('manager')
    )

    objects = StaffManager()

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = _('staff')
        verbose_name_plural = _('staff')
        indexes = [
            models.Index(fields=["username"]),
            models.Index(fields=["email"]),
            models.Index(fields=["phone"]),
            models.Index(fields=["active"]),
        ]

    def __str__(self):
        name = f"{self.first_name} {self.last_name or ''}".strip()
        return name or self.username

    def set_password(self, raw_password: str):
        self.password = make_password(raw_password)

    def check_password(self, raw_password: str) -> bool:
        return check_password(raw_password, self.password)

    def save(self, *args, **kwargs):
        if self.password and not self.password.startswith('pbkdf2_sha256$'):
            self.set_password(self.password)
        super().save(*args, **kwargs)
        
    class Meta:
        db_table = 'staff'
