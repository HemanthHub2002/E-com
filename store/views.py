from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from .models import Category, Product, Review, Wishlist
from .cart import Cart

def home_view(request):
    categories = Category.objects.all()
    products = Product.objects.filter(is_available=True)
    
    # Category Filter
    category_slug = request.GET.get('category')
    selected_category = None
    if category_slug:
        selected_category = get_object_or_404(Category, slug=category_slug)
        products = products.filter(category=selected_category)
        
    # Search Filter
    query = request.GET.get('q')
    if query:
        products = products.filter(
            Q(name__icontains=query) | 
            Q(description__icontains=query)
        )
        
    # Price Filter
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    if min_price:
        try:
            products = products.filter(price__gte=float(min_price))
        except ValueError:
            pass
    if max_price:
        try:
            products = products.filter(price__lte=float(max_price))
        except ValueError:
            pass

    # Availability filter
    in_stock = request.GET.get('in_stock')
    if in_stock == '1':
        products = products.filter(stock__gt=0)
        
    # Sorting
    sort_by = request.GET.get('sort')
    if sort_by == 'price_asc':
        products = products.order_by('price')
    elif sort_by == 'price_desc':
        products = products.order_by('-price')
    elif sort_by == 'newest':
        products = products.order_by('-created_at')
    
    # Extract unique values for filtering context
    return render(request, 'store/home.html', {
        'categories': categories,
        'products': products,
        'selected_category': selected_category,
        'sort_by': sort_by,
        'min_price': min_price,
        'max_price': max_price,
        'in_stock': in_stock,
    })


def product_detail_view(request, slug):
    product = get_object_or_404(Product, slug=slug, is_available=True)
    reviews = product.reviews.all()
    
    # Check if user has already reviewed the product
    user_review = None
    if request.user.is_authenticated:
        user_review = reviews.filter(user=request.user).first()
        
    # Wishlist status check
    in_wishlist = False
    if request.user.is_authenticated:
        in_wishlist = Wishlist.objects.filter(user=request.user, product=product).exists()
        
    return render(request, 'store/product_detail.html', {
        'product': product,
        'reviews': reviews,
        'user_review': user_review,
        'in_wishlist': in_wishlist,
    })


@login_required
def add_review_view(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    if request.method == 'POST':
        rating = request.POST.get('rating')
        comment = request.POST.get('comment', '').strip()
        
        if not rating:
            messages.error(request, "Please select a rating.")
            return redirect('store:product_detail', slug=product.slug)
            
        try:
            rating_val = int(rating)
            if rating_val < 1 or rating_val > 5:
                raise ValueError
        except ValueError:
            messages.error(request, "Invalid rating value.")
            return redirect('store:product_detail', slug=product.slug)

        # Check if user already reviewed
        review, created = Review.objects.update_or_create(
            product=product,
            user=request.user,
            defaults={'rating': rating_val, 'comment': comment}
        )
        
        if created:
            messages.success(request, "Thank you! Your review has been submitted.")
        else:
            messages.success(request, "Your review has been updated.")
            
    return redirect('store:product_detail', slug=product.slug)


# --- SHOPPING CART VIEWS ---

def cart_detail_view(request):
    return render(request, 'store/cart.html')


def cart_add_view(request, product_id):
    if request.user.is_authenticated and (request.user.is_staff or request.user.is_superuser):
        messages.error(request, "Administrators cannot add items to the cart or place orders.")
        return redirect('store:home')
        
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)
    quantity = 1
    
    if request.method == 'POST':
        quantity = int(request.POST.get('quantity', 1))
        
    cart.add(product=product, quantity=quantity)
    messages.success(request, f"{product.name} added to cart.")
    return redirect(request.META.get('HTTP_REFERER', 'store:cart_detail'))


def cart_update_view(request, product_id):
    if request.user.is_authenticated and (request.user.is_staff or request.user.is_superuser):
        messages.error(request, "Administrators cannot add items to the cart or place orders.")
        return redirect('store:home')
        
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)
    
    if request.method == 'POST':
        quantity = int(request.POST.get('quantity', 1))
        cart.add(product=product, quantity=quantity, override_quantity=True)
        messages.success(request, f"Updated quantity for {product.name}.")
        
    return redirect('store:cart_detail')


def cart_remove_view(request, product_id):
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)
    cart.remove(product)
    messages.info(request, f"{product.name} removed from cart.")
    return redirect('store:cart_detail')


# --- WISHLIST VIEWS ---

@login_required
def wishlist_view(request):
    wishlist_items = Wishlist.objects.filter(user=request.user)
    return render(request, 'store/wishlist.html', {'wishlist_items': wishlist_items})


@login_required
def toggle_wishlist_view(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    wishlist_item = Wishlist.objects.filter(user=request.user, product=product).first()
    
    if wishlist_item:
        wishlist_item.delete()
        messages.info(request, f"{product.name} removed from your wishlist.")
    else:
        Wishlist.objects.create(user=request.user, product=product)
        messages.success(request, f"{product.name} added to your wishlist.")
        
    return redirect(request.META.get('HTTP_REFERER', 'store:home'))
