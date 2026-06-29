from django.urls import path
from . import views

urlpatterns = [
    path('checkout/<int:package_id>/', views.checkout_view, name='checkout'),
    path('confirmation/<int:pk>/', views.booking_confirmation_view, name='booking_confirmation'),
    path('my-bookings/', views.my_bookings_view, name='my_bookings'),
    path('my-bookings/guest/', views.guest_bookings_view, name='guest_bookings'),
]
