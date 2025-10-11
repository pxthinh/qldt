from django.contrib import admin
from .models import Order, OrderItem

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('total_price',)
    fields = ('item_id', 'product', 'quantity', 'list_price', 'discount', 'total_price')

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('order_id', 'customer', 'order_status', 'order_date', 'total_amount')
    list_filter = ('order_status', 'order_date', 'store')
    search_fields = ('order_id', 'customer__first_name', 'customer__last_name', 'customer__email')
    date_hierarchy = 'order_date'
    inlines = [OrderItemInline]
    
    def total_amount(self, obj):
        return sum(item.total_price for item in obj.items.all())
    total_amount.short_description = 'Total Amount'

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'order', 'product', 'quantity', 'list_price', 'discount', 'total_price')
    list_filter = ('order__order_status',)
    search_fields = ('order__order_id', 'product__product_name')
    
    def total_price(self, obj):
        return obj.total_price
    total_price.short_description = 'Total Price'
