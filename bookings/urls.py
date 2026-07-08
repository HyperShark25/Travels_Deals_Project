from django.urls import path
from . import views

urlpatterns = [
    path('',views.home,name='home'),
    # Company pages
    path('company/<int:pk>/',views.company_detail_view,name='company_detail'),
    # Package pages
    path('package/<int:pk>/',views.package_detail_view,name='package_detail'),
    # Checkout & confirmation
    path('checkout/<int:package_id>/',views.checkout_view,name='checkout'),
    path('confirmation/<int:pk>/',views.booking_confirmation_view,name='booking_confirmation'),
    # Bookings
    path('my-bookings/',views.my_bookings_view,name='my_bookings'),
    path('my-bookings/guest/',views.guest_bookings_view,name='guest_bookings'),
    # Paymob
    path('payment/callback/',views.payment_callback_view,name='payment_callback'),
    path('payment/response/',views.payment_response,name='payment_response'),
]
