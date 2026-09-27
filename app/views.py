from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib import messages
from .forms import SignUpForm

# User: User
# Password for User: dasknfo23n!

# User: admin2
# Password for admin2: vgkig67o86o8

def login_user(request):
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, 'You have successfully logged in.')

            # After login, claim any guest bookings or reservations associated with the session
            _claim_guest_bookings(request, user)

            # next parameter is used to redirect the user to the page they were trying to access before login
            return redirect(request.GET.get('next', 'home'))  # Redirect to the next page or home

        messages.error(request, 'Invalid username or password. Please try again.')
    else:
        form = AuthenticationForm()

    return render(request, 'login.html', {'form': form})


def register_user(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)

            _claim_guest_bookings(request, user)

            messages.success(request, 'User created successfully.')
            return redirect('home')

        messages.error(request, 'Registration failed. Please correct the errors below.')
    else:
        form = SignUpForm()

    return render(request, 'register.html', {'form': form})



def logout_user(request):
    logout(request)
    messages.success(request, 'You have successfully logged out.')
    return redirect('home')



def _claim_guest_bookings(request, user):
    """
    This function should implement the logic to claim any guest bookings or reservations
    associated with the session(the bookings that were made while the user was a guest and
    after the user logs in or registers, we want to claim those bookings into the new
    user's account) and assign them to the new authenticated user( which is the logged-in user).
    """
    from bookings.models import Booking
    
    # ----> Very Important Note: The session_key is created in the booking.views.py file when a guest user makes a booking.
    
    # And here is where we are getting the session_key from the booking.views.py file and using it
    # to find any bookings that were made by the guest user and assigning them to the new authenticated user.
    session_key = request.session.session_key
    # And if there is no session_key, this means the user has no associated guest bookings and there's nothing to claim.
    if session_key:
        # Update the bookings that were made by the guest user and assign them to the new authenticated user.
        
        # We are filtering the bookings by session_key and user__isnull=True to find the bookings that were made by
        # the guest user and not yet claimed by any authenticated user.
        Booking.objects.filter(session_key=session_key, user__isnull=True).update(user=user)
