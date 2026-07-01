from django.shortcuts import render
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.models import User
from django.db.models import Sum
from .models import Product
from orders.models import Order

@user_passes_test(lambda u: u.is_staff, login_url='accounts:login')
def admin_dashboard_view(request):
    # Total Revenue (only paid orders)
    revenue_dict = Order.objects.filter(is_paid=True).aggregate(total_revenue=Sum('total'))
    total_revenue = revenue_dict['total_revenue'] or 0.00
    
    # Order statistics
    total_orders = Order.objects.count()
    status_counts = {
        'new': Order.objects.filter(status='New').count(),
        'paid': Order.objects.filter(status='Paid').count(),
        'shipped': Order.objects.filter(status='Shipped').count(),
        'delivered': Order.objects.filter(status='Delivered').count(),
        'cancelled': Order.objects.filter(status='Cancelled').count(),
    }
    
    # Low stock items list (stock < 5)
    low_stock_products = Product.objects.filter(stock__lt=5).order_by('stock')
    
    # User count
    total_users = User.objects.filter(is_staff=False).count()
    
    # Recent orders
    recent_orders = Order.objects.order_by('-created_at')[:5]
    
    return render(request, 'store/admin_dashboard.html', {
        'total_revenue': total_revenue,
        'total_orders': total_orders,
        'status_counts': status_counts,
        'low_stock_products': low_stock_products,
        'total_users': total_users,
        'recent_orders': recent_orders,
    })
