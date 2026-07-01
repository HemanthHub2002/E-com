import datetime
from django.db import models
from django.contrib.auth.models import User
from store.models import Product

class Order(models.Model):
    STATUS_CHOICES = (
        ('New', 'New/Unpaid'),
        ('Paid', 'Processing/Paid'),
        ('Shipped', 'Shipped'),
        ('Delivered', 'Delivered'),
        ('Cancelled', 'Cancelled'),
    )

    PAYMENT_CHOICES = (
        ('COD', 'Cash on Delivery'),
        ('Razorpay', 'Razorpay'),
    )

    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='orders')
    order_number = models.CharField(max_length=50, unique=True)
    shipping_address = models.TextField()  # JSON-formatted address snapshot
    
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    shipping = models.DecimalField(max_digits=10, decimal_places=2)
    tax = models.DecimalField(max_digits=10, decimal_places=2)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='New')
    payment_method = models.CharField(max_length=20, choices=PAYMENT_CHOICES, default='COD')
    payment_id = models.CharField(max_length=100, blank=True, null=True)
    is_paid = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Order #{self.order_number}"

    def save(self, *args, **kwargs):
        if not self.order_number:
            # Generate unique order number: ORD-YYYYMMDDHHMMSS-RAND
            import random
            timestamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
            rand_suffix = random.randint(1000, 9999)
            self.order_number = f"ORD-{timestamp}-{rand_suffix}"
        super().save(*args, **kwargs)


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True)
    quantity = models.IntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        product_name = self.product.name if self.product else "Deleted Product"
        return f"{product_name} ({self.quantity}) for Order #{self.order.order_number}"

    @property
    def total_price(self):
        if self.price is None:
            from decimal import Decimal
            return Decimal('0.00')
        return self.price * self.quantity
