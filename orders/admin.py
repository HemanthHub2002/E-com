from django.contrib import admin
from .models import Order, OrderItem

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('product', 'quantity', 'price', 'total_price')

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('order_number', 'user', 'total', 'status', 'payment_method', 'is_paid', 'created_at')
    list_filter = ('status', 'payment_method', 'is_paid')
    search_fields = ('order_number', 'user__username', 'payment_id')
    readonly_fields = ('order_number', 'shipping_address', 'subtotal', 'shipping', 'tax', 'total')
    inlines = [OrderItemInline]

