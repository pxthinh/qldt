from django.db import models
from django.contrib.auth.hashers import make_password, check_password

class Customer(models.Model):
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
