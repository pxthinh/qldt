from django.db import models
from django.contrib.auth.hashers import make_password, check_password

class Staff(models.Model):
    staff_id = models.AutoField(primary_key=True)

    username = models.CharField(max_length=150, unique=True, db_index=True)
    password = models.CharField(max_length=128)

    first_name = models.CharField(max_length=50)
    last_name  = models.CharField(max_length=50, blank=True, null=True)
    email = models.EmailField(max_length=254, blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    active = models.BooleanField(default=True)

    store = models.IntegerField(null=True, blank=True, db_column="store_id")

    manager = models.ForeignKey(
        'self', null=True, blank=True, on_delete=models.SET_NULL,
        db_column='manager_id', related_name='subordinates'
    )

    class Meta:
        verbose_name = "Staff"
        verbose_name_plural = "Staffs"
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
        if self.password and "$" not in self.password:
            self.password = make_password(self.password)
        super().save(*args, **kwargs)
