from decimal import Decimal
from django.conf import settings
from .models import Product

class Cart:
    def __init__(self, request):
        self.session = request.session
        cart = self.session.get('cart')
        if not cart:
            cart = self.session['cart'] = {}
        self.cart = cart
        self._clean_stale_items()

    def _clean_stale_items(self):
        if self.cart:
            product_ids = list(self.cart.keys())
            existing_ids = set(str(id_val) for id_val in Product.objects.filter(id__in=product_ids).values_list('id', flat=True))
            stale_ids = [pid for pid in product_ids if pid not in existing_ids]
            if stale_ids:
                for pid in stale_ids:
                    del self.cart[pid]
                self.save()

    def add(self, product, quantity=1, override_quantity=False):
        product_id = str(product.id)
        if product_id not in self.cart:
            self.cart[product_id] = {
                'quantity': 0,
                'price': str(product.price)
            }
        
        if override_quantity:
            self.cart[product_id]['quantity'] = quantity
        else:
            self.cart[product_id]['quantity'] += quantity
        
        # Check stock limits
        if self.cart[product_id]['quantity'] > product.stock:
            self.cart[product_id]['quantity'] = product.stock
            
        self.save()

    def save(self):
        self.session.modified = True

    def remove(self, product):
        product_id = str(product.id)
        if product_id in self.cart:
            del self.cart[product_id]
            self.save()

    def __iter__(self):
        product_ids = self.cart.keys()
        products = Product.objects.filter(id__in=product_ids)
        product_map = {str(p.id): p for p in products}

        for product_id, item_data in self.cart.items():
            product = product_map.get(product_id)
            if product:
                yield {
                    'product': product,
                    'quantity': item_data['quantity'],
                    'price': Decimal(item_data['price']),
                    'total_price': Decimal(item_data['price']) * item_data['quantity']
                }

    def __len__(self):
        return sum(item['quantity'] for item in self.cart.values())

    def get_subtotal_price(self):
        return sum(Decimal(item['price']) * item['quantity'] for item in self.cart.values())

    def get_shipping_price(self):
        subtotal = self.get_subtotal_price()
        if subtotal == 0:
            return Decimal('0.00')
        # Free shipping over $1000 or Rs. 1000
        if subtotal >= Decimal('1000.00'):
            return Decimal('0.00')
        return Decimal('100.00')  # Flat shipping rate

    def get_tax_price(self):
        # 18% GST/Tax estimation
        return (self.get_subtotal_price() * Decimal('0.18')).quantize(Decimal('0.01'))

    def get_total_price(self):
        return self.get_subtotal_price() + self.get_shipping_price() + self.get_tax_price()

    def clear(self):
        del self.session['cart']
        self.save()
