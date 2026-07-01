import json
from decimal import Decimal
from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse
from store.models import Category, Product
from orders.models import Order, OrderItem

class InvoiceTestCase(TestCase):
    def setUp(self):
        # 1. Create standard customer
        self.user1_password = 'customer1pass'
        self.user1 = User.objects.create_user(
            username='customer1',
            email='customer1@example.com',
            password=self.user1_password
        )
        
        # 2. Create another customer
        self.user2_password = 'customer2pass'
        self.user2 = User.objects.create_user(
            username='customer2',
            email='customer2@example.com',
            password=self.user2_password
        )
        
        # 3. Create staff user
        self.staff_password = 'staffpass123'
        self.staff_user = User.objects.create_user(
            username='staff_admin',
            email='staff@example.com',
            password=self.staff_password,
            is_staff=True
        )
        
        # 4. Setup catalog
        self.category = Category.objects.create(name='Apparel', slug='apparel')
        self.product = Product.objects.create(
            category=self.category,
            name='Monarch Watch',
            slug='monarch-watch',
            price=Decimal('189.50'),
            stock=10,
            is_available=True
        )
        
        # 5. Create shipping address snapshot
        address_dict = {
            'full_name': 'Hemanth',
            'phone_number': '8088725970',
            'street_address': 'doddadunnasandra',
            'city': 'bangalore',
            'state': 'karnataka',
            'postal_code': '560067',
            'country': 'India',
        }
        self.address_json = json.dumps(address_dict)
        
        # 6. Create Order for Customer 1
        self.order1 = Order.objects.create(
            user=self.user1,
            order_number='ORD-20260701204713-2501',
            shipping_address=self.address_json,
            payment_method='Razorpay',
            subtotal=Decimal('189.50'),
            shipping=Decimal('100.00'),
            tax=Decimal('34.11'),
            total=Decimal('323.61'),
            is_paid=True,
            status='Delivered'
        )
        OrderItem.objects.create(
            order=self.order1,
            product=self.product,
            price=Decimal('189.50'),
            quantity=1
        )

    def test_anonymous_user_redirected_to_login(self):
        url = reverse('orders:download_invoice', kwargs={'order_number': self.order1.order_number})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('accounts:login'), response.url)

    def test_owner_can_download_invoice(self):
        self.client.login(username='customer1', password=self.user1_password)
        url = reverse('orders:download_invoice', kwargs={'order_number': self.order1.order_number})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'INV-2501')
        self.assertContains(response, 'Monarch Watch')

    def test_other_customer_cannot_download_invoice(self):
        self.client.login(username='customer2', password=self.user2_password)
        url = reverse('orders:download_invoice', kwargs={'order_number': self.order1.order_number})
        response = self.client.get(url)
        # Returns 404 since customer 2 does not own the order
        self.assertEqual(response.status_code, 404)

    def test_staff_member_can_download_any_invoice(self):
        self.client.login(username='staff_admin', password=self.staff_password)
        url = reverse('orders:download_invoice', kwargs={'order_number': self.order1.order_number})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'INV-2501')
