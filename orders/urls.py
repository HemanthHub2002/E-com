from django.urls import path
from . import views

app_name = 'orders'

urlpatterns = [
    path('checkout/', views.checkout_view, name='checkout'),
    path('place-order/', views.place_order_view, name='place_order'),
    path('payment/verify/', views.payment_verify_view, name='payment_verify'),
    path('success/<str:order_number>/', views.order_success_view, name='order_success'),
    path('detail/<str:order_number>/', views.order_detail_view, name='order_detail'),
    path('cancel/<str:order_number>/', views.cancel_order_view, name='cancel_order'),
    path('invoice/<str:order_number>/', views.download_invoice_view, name='download_invoice'),
]
