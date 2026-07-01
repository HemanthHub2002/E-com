import os
import django

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce.settings')
django.setup()

from django.utils.text import slugify
from django.contrib.auth.models import User
from store.models import Category, Product

def seed_db():
    print("Seeding database...")
    
    # 1. Clear existing products & categories
    Product.objects.all().delete()
    Category.objects.all().delete()
    
    # Create default admin and customer
    if not User.objects.filter(username='admin').exists():
        User.objects.create_superuser('admin', 'admin@ecom.com', 'adminpass')
        print("Superuser 'admin' created.")
    if not User.objects.filter(username='customer').exists():
        User.objects.create_user('customer', 'customer@ecom.com', 'customerpass')
        print("Customer user 'customer' created.")
    
    # 2. Create Categories
    categories_data = [
        {'name': 'Electronics', 'description': 'Gadgets, smartphones, audio systems and state of the art technology.'},
        {'name': 'Fashion', 'description': 'Premium clothing, accessories, footwear and watches.'},
        {'name': 'Home & Living', 'description': 'Architectural furniture, kitchen appliances, and lifestyle decors.'},
    ]
    
    created_categories = {}
    for cat_info in categories_data:
        cat, created = Category.objects.get_or_create(
            name=cat_info['name'],
            defaults={
                'slug': slugify(cat_info['name']),
                'description': cat_info['description']
            }
        )
        created_categories[cat.name] = cat
        print(f"Category '{cat.name}' created.")

    # 3. Create Products
    products_data = [
        {
            'category': created_categories['Electronics'],
            'name': 'AeroSpace Wireless Headphones',
            'description': 'Studio-grade noise-cancelling headphones featuring 40h battery life, dynamic spatial audio, and premium memory foam padding.',
            'price': 249.99,
            'stock': 12,
            'image': 'products/headphones.png',
        },
        {
            'category': created_categories['Electronics'],
            'name': 'Sonic SoundBuds Pro',
            'description': 'True wireless earbuds with active background isolation, custom ambient pass-through, and waterproof casing rating IPX7.',
            'price': 129.99,
            'stock': 0, # Sold Out
            'image': 'products/earbuds.png',
        },
        {
            'category': created_categories['Fashion'],
            'name': 'Monarch Quartz Chronograph',
            'description': 'Minimalist wristwatch crafted with medical-grade stainless steel casing, genuine Italian leather strap, and sapphire crystal glass.',
            'price': 189.50,
            'stock': 3, # Low Stock
            'image': 'products/watch.png',
        },
        {
            'category': created_categories['Fashion'],
            'name': 'E-com Leather Commuter Pack',
            'description': 'Water-resistant full-grain leather backpack featuring dedicated laptop protective chambers, hidden security pocket, and ergonomic support.',
            'price': 159.00,
            'stock': 7,
            'image': 'products/backpack.png',
        },
        {
            'category': created_categories['Home & Living'],
            'name': 'Aroma Drip Smart Brewer',
            'description': 'Wi-Fi enabled customizable coffee maker with precision temperature selectors, automatic scheduling, and integrated bean grinder.',
            'price': 89.99,
            'stock': 2, # Low Stock
            'image': 'products/coffeemaker.png',
        },
        {
            'category': created_categories['Home & Living'],
            'name': 'Zenith Ergonomic Desk Chair',
            'description': 'Adaptive mesh lumbar support office chair with fully-adjustable armrests, weight-sensitive tilt limits, and aluminum gas cylinder mechanism.',
            'price': 349.00,
            'stock': 15,
            'image': 'products/chair.png',
        },
    ]

    for prod_info in products_data:
        prod = Product.objects.create(
            category=prod_info['category'],
            name=prod_info['name'],
            slug=slugify(prod_info['name']),
            description=prod_info['description'],
            price=prod_info['price'],
            stock=prod_info['stock'],
            image=prod_info.get('image'),
            is_available=True
        )
        print(f"Product '{prod.name}' created.")
        
    print("Database seeding completed successfully.")

if __name__ == '__main__':
    seed_db()
