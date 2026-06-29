from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Booking, VacationPackage


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
                user=None,
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
        
        # TODO: hand off to paymob here, passing the booking.pk
        return redirect('booking_confirmation', pk=booking.id)
    
    return render(request, 'bookings/checkout.html', {'package': package})



def booking_confirmation_view(request, pk):
    booking = get_object_or_404(Booking, pk=pk)
    return render(request, 'bookings/confirmation.html', {'booking': booking})



@login_required
def my_bookings_view(request):    
    # The select_related('package__company') is used to optimize database queries by fetching related package and company data in a single query, reducing
    # the number of database hits(It does not change the result of the query at all, it just helps the performance).
    # Finally, we order the bookings by their creation date in descending order so that the most recent bookings appear first.
    bookings = Booking.objects.filter(user=request.user).select_related('package__company').order_by('-created_at')
    return render(request, 'bookings/my_bookings.html', {'bookings': bookings})



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
    return render(request, 'bookings/guest_bookings.html', {'bookings': bookings})
