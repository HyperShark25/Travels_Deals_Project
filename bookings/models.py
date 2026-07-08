from django.db import models
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User


class TravelCompany(models.Model):
    name = models.CharField(max_length=100, unique=True)
    logo = models.ImageField(upload_to='logos/', blank=True, null=True)
    description = models.TextField(max_length=1000, blank=True, null=True)
    managers = models.ManyToManyField(
        User,
        blank=True,
        related_name='managed_companies',
        help_text='Staff members who can manage this travel company.'
    )

    def __str__(self):
        return self.name


class VacationPackage(models.Model):
    company = models.ForeignKey(TravelCompany, on_delete=models.CASCADE)
    title = models.CharField(max_length=100)
    description = models.TextField(max_length=1000, blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    start_date = models.DateField()
    end_date = models.DateField()

    def __str__(self):
        return f"{self.title} - {self.company.name}"
    
    # If we create an object manually like VacationPackage.objects.create(...)
    # , the clean method will not be called automatically. Therefore, we need
    # to call full_clean() before save() in the views.py to ensure validation is performed.
    def clean(self):
        if self.start_date > self.end_date:
            raise ValidationError('Start date must be before end date.')


class Booking(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('cancelled', 'Cancelled'),
    ]
    package = models.ForeignKey(VacationPackage, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    
    # If the user is not logged in, we can still allow them to make a booking by
    # providing their name and email.
    guest_name = models.CharField(max_length=100, blank=True, null=True)
    guest_email = models.EmailField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    paymob_order_id = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    session_key = models.CharField(max_length=40, blank=True, null=True)

    def __str__(self):
        return f'Booking for Package: {self.package.title} Related to Company: {self.package.company.name}'
