from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import RegistrationForm, LoginForm, AddressForm
from .models import Address
from orders.models import Order  # Imported to show order history

def register_view(request):
    if request.user.is_authenticated:
        return redirect('store:home')
    
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f"Welcome, {user.username}! Your account has been created.")
            return redirect('store:home')
    else:
        form = RegistrationForm()
    
    return render(request, 'accounts/register.html', {'form': form})

def login_view(request):
    if request.user.is_authenticated:
        return redirect('store:home')
    
    next_url = request.GET.get('next', 'store:home')
    
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f"Welcome back, {user.username}!")
                return redirect(next_url)
            else:
                messages.error(request, "Invalid username or password.")
    else:
        form = LoginForm()
        
    return render(request, 'accounts/login.html', {'form': form, 'next': next_url})

def logout_view(request):
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect('store:home')

@login_required
def profile_view(request):
    addresses = Address.objects.filter(user=request.user)
    # Fetch user's orders, sorted by newest
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    
    return render(request, 'accounts/profile.html', {
        'addresses': addresses,
        'orders': orders
    })

@login_required
def add_address_view(request):
    if request.method == 'POST':
        form = AddressForm(request.POST)
        if form.is_valid():
            address = form.save(commit=False)
            address.user = request.user
            address.save()
            messages.success(request, "Address added successfully.")
            return redirect('accounts:profile')
    else:
        form = AddressForm()
    
    return render(request, 'accounts/address_form.html', {'form': form, 'title': 'Add New Address'})

@login_required
def delete_address_view(request, pk):
    address = get_object_or_404(Address, pk=pk, user=request.user)
    address.delete()
    messages.success(request, "Address deleted successfully.")
    return redirect('accounts:profile')
