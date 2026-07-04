from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse

from .models import Booking, TravelCompany, VacationPackage


class BillingInfoViewTests(TestCase):
    def setUp(self):
        self.company = TravelCompany.objects.create(name='Test Company')
        self.package = VacationPackage.objects.create(
            company=self.company,
            title='Beach Escape',
            description='Relaxing getaway',
            price='125.50',
            start_date='2026-01-01',
            end_date='2026-01-10',
        )

    @patch('bookings.views.get_payment_key')
    @patch('bookings.views.register_order')
    @patch('bookings.views.get_auth_token')
    def test_billing_info_creates_booking_and_builds_paymob_items(self, mock_auth_token, mock_register_order, mock_get_payment_key):
        mock_auth_token.return_value = 'fake-auth-token'
        mock_register_order.return_value = 42
        mock_get_payment_key.return_value = 'fake-payment-token'

        response = self.client.post(
            reverse('billing_info', args=[self.package.id]),
            {'name': 'Ada Lovelace', 'email': 'ada@example.com'},
        )

        self.assertEqual(response.status_code, 302)
        booking = Booking.objects.get()
        self.assertEqual(booking.guest_name, 'Ada Lovelace')
        self.assertEqual(booking.guest_email, 'ada@example.com')
        self.assertEqual(booking.status, 'pending')

        mock_register_order.assert_called_once()
        _, amount_cents, merchant_order_id, items = mock_register_order.call_args.args
        self.assertEqual(amount_cents, 12550)
        self.assertEqual(merchant_order_id, str(booking.id))
        self.assertEqual(items[0]['name'], self.package.title)
        self.assertEqual(items[0]['amount_cents'], 12550)
