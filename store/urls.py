from django.urls import path
from . import views, admin_views

app_name = 'store'

urlpatterns = [
    path('', views.home_view, name='home'),
    path('product/<slug:slug>/', views.product_detail_view, name='product_detail'),
    path('product/<int:product_id>/review/', views.add_review_view, name='add_review'),
    path('cart/', views.cart_detail_view, name='cart_detail'),
    path('cart/add/<int:product_id>/', views.cart_add_view, name='cart_add'),
    path('cart/update/<int:product_id>/', views.cart_update_view, name='cart_update'),
    path('cart/remove/<int:product_id>/', views.cart_remove_view, name='cart_remove'),
    path('wishlist/', views.wishlist_view, name='wishlist'),
    path('wishlist/toggle/<int:product_id>/', views.toggle_wishlist_view, name='toggle_wishlist'),
    path('dashboard/', admin_views.admin_dashboard_view, name='admin_dashboard'),
]
