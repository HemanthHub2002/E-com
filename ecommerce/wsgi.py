"""
WSGI config for ecommerce project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/howto/deployment/wsgi/
"""
import os
import tempfile
import django
from django.core.management import call_command
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce.settings')

# Auto-migrate and seed on startup (especially for ephemeral sqlite databases on Render)
lock_file = os.path.join(tempfile.gettempdir(), 'django_db_init.lock')
if not os.path.exists(lock_file):
    try:
        fd = os.open(lock_file, os.O_CREAT | os.O_WRONLY | os.O_EXCL)
        os.write(fd, b'locked')
        os.close(fd)
        
        print("Auto-initializing database from WSGI...")
        django.setup()
        
        # Run migrations
        call_command('migrate', interactive=False)
        
        # Seed database if it has no products
        from store.models import Product
        if not Product.objects.exists():
            print("Database is empty. Seeding...")
            from seed_store import seed_db
            from seed_gallery import seed_product_gallery
            seed_db()
            seed_product_gallery()
        print("WSGI database auto-initialization complete.")
    except (FileExistsError, OSError):
        # Another worker is already initializing or lock exists
        pass
    except Exception as e:
        print(f"WSGI database auto-initialization failed: {e}")
        try:
            os.remove(lock_file)
        except OSError:
            pass

application = get_wsgi_application()
