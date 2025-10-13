from django.contrib import admin
from .models import Store


@admin.register(Store)
class StoreAdmin(admin.ModelAdmin):
    list_display = ('store_name', 'city', 'state', 'phone', 'email')
    search_fields = ('store_name', 'city', 'state', 'zip_code')
    list_filter = ('state', 'city')
    ordering = ('store_name',)
    fieldsets = (
        (None, {
            'fields': ('store_name', 'phone', 'email')
        }),
        ('Address Information', {
            'fields': ('street', 'city', 'state', 'zip_code')
        }),
    )
    readonly_fields = ('created_at', 'updated_at')
