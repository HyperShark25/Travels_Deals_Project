from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .paymob import get_auth_token, create_order, get_payment_key
from .models import *
from django.conf import settings
from . import paymob
import json
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse



def home(request):
    bookings = Booking.objects.all()
    VacationPackages = VacationPackage.objects.all()
    return render(request, 'index.html', {'bookings': bookings, 'vacation_packages': VacationPackages})


def package_detail_view(request, pk):
    package = get_object_or_404(VacationPackage, id=pk)
    return render(request, 'package_detail.html', {'package': package})


def company_detail_view(request, company_id):
    company = get_object_or_404(TravelCompany, id=company_id)
    return render(request, 'company_detail.html', {'company': company})


@csrf_exempt
def payment_callback_view(request):
    if request.method != 'POST':
        return HttpResponse(status=405)

    data = json.loads(request.body)
    transaction = data.get('obj', {})

    # Verify HMAC — reject anything that doesn't match
    if not paymob.verify_hmac(request.GET):
        return HttpResponse(status=403)

    paymob_order_id = str(transaction.get('order', {}).get('id', ''))
    success         = transaction.get('success', False)

    try:
        booking = Booking.objects.get(paymob_order_id=paymob_order_id)
    except Booking.DoesNotExist:
        return HttpResponse(status=404)

    booking.status = 'paid' if success else 'cancelled'
    booking.save()

    return HttpResponse(status=200)


def payment_response(request):
    """
    Paymob redirects the user's browser here after the iframe.
    Use this only to show a message — don't update booking status here.
    """
    success = request.GET.get('success') == 'true'
    return render(request, 'bookings/payment_result.html', {'success': success})


# Come back to this function later to add payment integration with Paymob
def checkout_view(request, package_id):
    package = get_object_or_404(VacationPackage, id=package_id)

    if request.method == 'POST':
        # Ensure the session exists so we can get the session key
        if not request.session.session_key:
            request.session.create()
        
        if request.user.is_authenticated:
            booking = Booking.objects.create(
                package=package,
                user=request.user,
                status='pending',
            )
        
        else:
            # guest booking - store name and email and tie to the session

            # Any time we have something like .get('name', '') or .get('email', ''),
            # it means we are trying to retrieve a value from the POST data sent by
            # the form submission. The first argument is the key we are looking for
            # (in this case, 'name' or 'email'), and the second argument is a default
            # value to return if that key doesn't exist in the POST data. In this case,
            # if the user didn't provide a name or email, it will default to an empty
            # string.
            booking = Booking.objects.create(
                package=package,
                guest_name=request.POST.get('name', ''),
                guest_email=request.POST.get('email', ''),
                session_key=request.session.session_key,
                status='pending',
            )

            # Keep a list of guest bookings IDs in the session for later reference
            
            # request.session.get('guest_booking_ids', []) basically says:-
            # Give me the value for this key( first argument). If the key doesn't exist,
            # just give me this default value( second argument) instead.

            # 1st line of code retrieve the existing list from the session which is
            # stored under the key "guest_booking_ids", or return a temporary empty
            # list if the key doesn't exist.

            # 2nd line of code appends the new booking's ID to the list.

            # 3rd line of code saves the updated list back into the session under the
            # same key.
            
            guest_ids = request.session.get('guest_booking_ids', [])
            guest_ids.append(booking.id)
            request.session['guest_booking_ids'] = guest_ids
        
        # Build the billing data
        if request.user.is_authenticated:
            billing_data = {
                'first_name': request.user.first_name or 'NA',
                'last_name': request.user.last_name or 'NA',
                'email': request.user.email,
                'phone_number': 'NA',
                'apartment': 'NA',
                'floor': 'NA',
                'street': 'NA',
                'building': 'NA',
                'city': 'NA',
                'country': 'NA',
            }
        
        else:
            name_parts = booking.guest_name.split(' ', 1)
            billing_data = {
                'first_name': name_parts[0],
                'last_name': name_parts[1] if len(name_parts) > 1 else 'NA',
                'email': booking.guest_email,
                'phone_number': 'NA',
                'apartment': 'NA',
                'floor': 'NA',
                'street': 'NA',
                'building': 'NA',
                'city': 'NA',
                'country': 'NA',
            }
        # Paymob expects the amount in cents, so we multiply by 100
        amount_cents = int(package.price * 100)

        # Run the 3 steps to get the payment key from Paymob
        auth_token = get_auth_token()
        paymob_order_id = create_order(auth_token, amount_cents, booking.pk)
        payment_key = get_payment_key(auth_token, paymob_order_id, amount_cents, billing_data)

        # Save the Paymob order ID and payment key in the booking for later reference
        booking.paymob_order_id = str(paymob_order_id)
        booking.save()

        # Redirect tp Paymob iframe
        iframe_url = f"https://accept.paymob.com/api/acceptance/iframes/{settings.PAYMOB_IFRAME_ID}?payment_token={payment_key}"
        return redirect(iframe_url)
    
    return render(request, 'checkout.html', {'package': package})



def booking_confirmation_view(request, pk):
    booking = get_object_or_404(Booking, pk=pk)
    return render(request, 'confirmation.html', {'booking': booking})



@login_required
def my_bookings_view(request):    
    # The select_related('package__company') is used to optimize database queries by fetching related package and company data in a
    # single query, reducing the number of database hits(It does not change the result of the query at all, it just helps the performance).
    # Finally, we order the bookings by their creation date in descending order so that the most recent bookings appear first.
    bookings = Booking.objects.filter(user=request.user).select_related('package__company').order_by('-created_at')
    return render(request, 'my_bookings.html', {'bookings': bookings})



def guest_bookings_view(request):
    """
    Lets guests view their bookings for the current session,
    without needing to log in.
    """
    # Why we need to use request.session.get('guest_booking_ids', []) instead of just request.session['guest_booking_ids']
    # The .get('guest_booking_ids', []) default in guest_bookings_view is just a defensive fallback for edge cases like:

    # A user navigates directly to /my-bookings/guest/ without ever checking out
    # The session expired and Django started a fresh one
    # Someone clears their cookies mid-session

    # The __in lookup can be used anytime we want to filter a queryset based on a list of values or generally multiple values.
    guest_ids = request.session.get('guest_booking_ids', [])
    bookings  = Booking.objects.filter(pk__in=guest_ids).select_related('package__company')
    return render(request, 'guest_bookings.html', {'bookings': bookings})
