import os
import django

# Configure django settings environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce.settings')
django.setup()

from store.models import Product, ProductImage
from django.core.files import File

def seed_product_gallery():
    products = Product.objects.all()
    print(f"Found {products.count()} product(s) to seed.")
    
    for product in products:
        if product.image and os.path.exists(product.image.path):
            # Clean old gallery images
            product.gallery_images.all().delete()
            
            # Seed 2 gallery images
            for i in range(1, 3):
                with open(product.image.path, 'rb') as f:
                    gallery_file = File(f)
                    gallery_img = ProductImage(product=product)
                    filename = f"{product.slug}_gallery_{i}.png"
                    gallery_img.image.save(filename, gallery_file, save=True)
            print(f"[SUCCESS] Seeded 2 gallery images for: {product.name}")
        else:
            print(f"[ERROR] Product {product.name} has no main image or file path is missing.")

if __name__ == '__main__':
    seed_product_gallery()
    print("Gallery seeding completed successfully!")
