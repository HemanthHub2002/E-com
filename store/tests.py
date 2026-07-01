from decimal import Decimal
from django.test import TestCase, RequestFactory
from django.contrib.auth.models import User
from django.contrib.sessions.middleware import SessionMiddleware
from django.urls import reverse

from store.models import Category, Product
from store.cart import Cart
from orders.models import Order, OrderItem

class ECommerceTestCase(TestCase):
    def setUp(self):
        # Initialize Request Factory and Database Seed
        self.factory = RequestFactory()
        
        # 1. Create a User
        self.user_password = 'testpassword123'
        self.user = User.objects.create_user(
            username='john_doe',
            email='john@example.com',
            password=self.user_password
        )
        
        # 2. Create Category and Product
        self.category = Category.objects.create(name='Tech', slug='tech')
        self.product = Product.objects.create(
            category=self.category,
            name='Quantum Earbuds',
            slug='quantum-earbuds',
            price=Decimal('100.00'),
            stock=10,
            is_available=True
        )

    def test_cart_operations(self):
        # Simulate request with session
        request = self.factory.get('/')
        middleware = SessionMiddleware(lambda req: None)
        middleware.process_request(request)
        request.session.save()
        
        # Initialize Cart
        cart = Cart(request)
        self.assertEqual(len(cart), 0)
        self.assertEqual(cart.get_subtotal_price(), Decimal('0.00'))
        
        # Add Product to Cart
        cart.add(product=self.product, quantity=2)
        self.assertEqual(len(cart), 2)
        self.assertEqual(cart.get_subtotal_price(), Decimal('200.00'))
        
        # Check overall billing calculations
        # Subtotal: 200.00
        # Tax: 18% of 200.00 = 36.00
        # Shipping: 100.00 (since 200.00 < 1000.00 threshold)
        # Total: 336.00
        self.assertEqual(cart.get_tax_price(), Decimal('36.00'))
        self.assertEqual(cart.get_shipping_price(), Decimal('100.00'))
        self.assertEqual(cart.get_total_price(), Decimal('336.00'))
        
        # Adjust quantity override
        cart.add(product=self.product, quantity=5, override_quantity=True)
        self.assertEqual(len(cart), 5)
        
        # Remove item
        cart.remove(self.product)
        self.assertEqual(len(cart), 0)

    def test_protected_routes_anonymous_redirect(self):
        # 1. Checkout view requires authentication
        response = self.client.get(reverse('orders:checkout'))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('accounts:login'), response.url)

        # 2. Wishlist view requires authentication
        response = self.client.get(reverse('store:wishlist'))
        self.assertEqual(response.status_code, 302)
        
    def test_staff_dashboard_authorization(self):
        # Non-staff user login
        self.client.login(username='john_doe', password=self.user_password)
        
        # Accessing staff dashboard should redirect (302) to login URL
        response = self.client.get(reverse('store:admin_dashboard'))
        self.assertEqual(response.status_code, 302)
        
        # Upgrade user to staff status
        self.user.is_staff = True
        self.user.save()
        
        # Staff dashboard should now serve page successfully (200)
        response = self.client.get(reverse('store:admin_dashboard'))
        self.assertEqual(response.status_code, 200)

    def test_order_creation_stock_reduction(self):
        # Log the user in
        self.client.login(username='john_doe', password=self.user_password)
        
        # Add Address
        address = self.user.addresses.create(
            full_name='John Doe',
            phone_number='1234567890',
            street_address='123 Cyber St',
            city='Neo Delhi',
            state='Delhi',
            postal_code='110001',
            country='India',
            is_default=True
        )
        
        # Populate session cart using request object
        session = self.client.session
        session['cart'] = {
            str(self.product.id): {
                'quantity': 3,
                'price': str(self.product.price)
            }
        }
        session.save()
        
        # Place order via POST COD
        post_data = {
            'shipping_address': address.id,
            'payment_method': 'COD'
        }
        
        response = self.client.post(reverse('orders:place_order'), post_data)
        
        # Should redirect to success page
        self.assertEqual(response.status_code, 302)
        
        # Verify order records created
        order = Order.objects.filter(user=self.user).first()
        self.assertIsNotNone(order)
        self.assertEqual(order.payment_method, 'COD')
        self.assertEqual(order.total, Decimal('454.00')) # Subtotal: 300, Tax: 54, Shipping: 100
        
        # Verify product inventory stock reduction (10 initial - 3 ordered = 7 remaining)
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 7)
