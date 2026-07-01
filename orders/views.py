import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.conf import settings
from store.cart import Cart
from accounts.models import Address
from accounts.forms import AddressForm
from .models import Order, OrderItem

import razorpay

@login_required
def checkout_view(request):
    if request.user.is_staff or request.user.is_superuser:
        messages.error(request, "Administrators cannot add items to the cart or place orders.")
        return redirect('store:home')
        
    cart = Cart(request)
    if len(cart) == 0:
        messages.warning(request, "Your cart is empty. Add some products before checking out.")
        return redirect('store:cart_detail')
        
    addresses = Address.objects.filter(user=request.user)
    address_form = AddressForm()
    
    return render(request, 'orders/checkout.html', {
        'addresses': addresses,
        'address_form': address_form,
    })

@login_required
def place_order_view(request):
    if request.user.is_staff or request.user.is_superuser:
        messages.error(request, "Administrators cannot add items to the cart or place orders.")
        return redirect('store:home')
        
    cart = Cart(request)
    if len(cart) == 0:
        return redirect('store:cart_detail')
        
    if request.method == 'POST':
        address_id = request.POST.get('shipping_address')
        payment_method = request.POST.get('payment_method')
        
        # 1. Fetch or create address
        if address_id == 'new':
            form = AddressForm(request.POST)
            if form.is_valid():
                address_obj = form.save(commit=False)
                address_obj.user = request.user
                address_obj.save()
            else:
                messages.error(request, "Please correct the errors in the address form.")
                return redirect('orders:checkout')
        else:
            address_obj = get_object_or_404(Address, id=address_id, user=request.user)
            
        # Serialize address to JSON snapshot
        address_snapshot = {
            'full_name': address_obj.full_name,
            'phone_number': address_obj.phone_number,
            'street_address': address_obj.street_address,
            'city': address_obj.city,
            'state': address_obj.state,
            'postal_code': address_obj.postal_code,
            'country': address_obj.country,
        }
        
        # 2. Create the Order
        order = Order.objects.create(
            user=request.user,
            shipping_address=json.dumps(address_snapshot),
            subtotal=cart.get_subtotal_price(),
            shipping=cart.get_shipping_price(),
            tax=cart.get_tax_price(),
            total=cart.get_total_price(),
            payment_method=payment_method,
            status='New',
            is_paid=False
        )
        
        # 3. Create OrderItems
        for item in cart:
            OrderItem.objects.create(
                order=order,
                product=item['product'],
                quantity=item['quantity'],
                price=item['price']
            )
            
        # 4. Handle Payment Methods
        if payment_method == 'COD':
            # Cash on Delivery: Success directly
            # Deduct stock
            for item in order.items.all():
                product = item.product
                product.stock -= item.quantity
                if product.stock < 0:
                    product.stock = 0
                product.save()
                
            cart.clear()
            messages.success(request, f"Order placed successfully using Cash on Delivery. Order ID: #{order.order_number}")
            return redirect('orders:order_success', order_number=order.order_number)
            
        elif payment_method == 'Razorpay':
            # Initialize Razorpay order
            amount_paise = int(order.total * 100)
            
            # Setup Razorpay client details
            try:
                client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
                razorpay_order = client.order.create({
                    'amount': amount_paise,
                    'currency': 'INR',
                    'payment_capture': '1'
                })
                razorpay_order_id = razorpay_order['id']
                is_mock = False
            except Exception as e:
                # Fallback to mock order flow if Razorpay client fails (e.g. invalid keys or network errors)
                import uuid
                razorpay_order_id = f"rzp_mock_{uuid.uuid4().hex[:12]}"
                is_mock = True
                
            order.payment_id = razorpay_order_id
            order.save()
            
            # Render payment processing screen with order details
            return render(request, 'orders/payment.html', {
                'order': order,
                'razorpay_order_id': razorpay_order_id,
                'razorpay_key_id': settings.RAZORPAY_KEY_ID,
                'amount_paise': amount_paise,
                'is_mock': is_mock,
            })
            
    return redirect('orders:checkout')

@login_required
def payment_verify_view(request):
    if request.method == 'POST':
        order_id = request.POST.get('order_id')
        payment_id = request.POST.get('payment_id')
        signature = request.POST.get('signature')
        status = request.POST.get('status') # 'success' or 'fail' from simulated flow
        
        order = get_object_or_404(Order, order_number=order_id, user=request.user)
        
        if status == 'fail':
            order.status = 'Cancelled'
            order.save()
            messages.error(request, "Payment failed. The order has been cancelled.")
            return render(request, 'orders/payment_failed.html', {'order': order})
            
        # Verify payment signature if it is a real razorpay transaction
        is_verified = False
        if order.payment_id and order.payment_id.startswith('rzp_mock_'):
            # Simulated payment verification
            is_verified = (status == 'success')
        else:
            try:
                client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
                params_dict = {
                    'razorpay_order_id': order.payment_id,
                    'razorpay_payment_id': payment_id,
                    'razorpay_signature': signature
                }
                client.utility.verify_payment_signature(params_dict)
                is_verified = True
            except Exception:
                is_verified = False
                
        if is_verified:
            order.is_paid = True
            order.status = 'Paid'
            order.payment_id = payment_id or order.payment_id
            order.save()
            
            # Reduce inventory stock
            for item in order.items.all():
                product = item.product
                product.stock -= item.quantity
                if product.stock < 0:
                    product.stock = 0
                product.save()
                
            # Clear Cart
            cart = Cart(request)
            cart.clear()
            
            messages.success(request, f"Payment verified! Order placed successfully. ID: #{order.order_number}")
            return redirect('orders:order_success', order_number=order.order_number)
        else:
            order.status = 'Cancelled'
            order.save()
            messages.error(request, "Payment signature verification failed. Please try again.")
            return render(request, 'orders/payment_failed.html', {'order': order})
            
    return redirect('store:home')

@login_required
def order_success_view(request, order_number):
    order = get_object_or_404(Order, order_number=order_number, user=request.user)
    address_snapshot = json.loads(order.shipping_address)
    
    return render(request, 'orders/order_success.html', {
        'order': order,
        'address': address_snapshot
    })

@login_required
def order_detail_view(request, order_number):
    order = get_object_or_404(Order, order_number=order_number, user=request.user)
    address_snapshot = json.loads(order.shipping_address)
    
    return render(request, 'orders/order_detail.html', {
        'order': order,
        'address': address_snapshot
    })

@login_required
def cancel_order_view(request, order_number):
    order = get_object_or_404(Order, order_number=order_number, user=request.user)
    
    # Check if order is eligible to be cancelled (only if status is New or Paid)
    if order.status in ['New', 'Paid']:
        order.status = 'Cancelled'
        order.save()
        
        # Restore items stock count
        for item in order.items.all():
            product = item.product
            product.stock += item.quantity
            product.save()
            
        messages.success(request, f"Order #{order.order_number} has been cancelled and stock has been restored.")
    else:
        messages.error(request, f"Order #{order.order_number} cannot be cancelled as it is already {order.status.lower()}.")
        
    return redirect('accounts:profile')


@login_required
def download_invoice_view(request, order_number):
    if request.user.is_staff or request.user.is_superuser:
        order = get_object_or_404(Order, order_number=order_number)
    else:
        order = get_object_or_404(Order, order_number=order_number, user=request.user)
        
    address_snapshot = json.loads(order.shipping_address)
    
    return render(request, 'orders/invoice.html', {
        'order': order,
        'address': address_snapshot
    })
