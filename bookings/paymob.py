# bookings/paymob.py
import hmac
import hashlib
import requests
from django.conf import settings

PAYMOB_BASE = 'https://accept.paymob.com/api'


def get_auth_token():
    response = requests.post(
        f'{PAYMOB_BASE}/auth/tokens',
        json={'api_key': settings.PAYMOB_API_KEY},
    )
    response.raise_for_status()
    return response.json()['token']


def create_order(auth_token, amount_cents, booking_id):
    response = requests.post(
        f'{PAYMOB_BASE}/ecommerce/orders',
        json={
            'auth_token':        auth_token,
            'delivery_needed':   False,
            'amount_cents':      amount_cents,
            'currency':          'EGP',
            'merchant_order_id': str(booking_id),  # your internal booking ID
            'items':             [],
        },
    )
    response.raise_for_status()
    return response.json()['id']  # Paymob order ID


def get_payment_key(auth_token, paymob_order_id, amount_cents, billing_data):
    response = requests.post(
        f'{PAYMOB_BASE}/acceptance/payment_keys',
        json={
            'auth_token':       auth_token,
            'amount_cents':     amount_cents,
            'expiration':       3600,
            'order_id':         paymob_order_id,
            'billing_data':     billing_data,
            'currency':         'EGP',
            'integration_id':   settings.PAYMOB_INTEGRATION_ID,
        },
    )
    response.raise_for_status()
    return response.json()['token']


def verify_hmac(data: dict) -> bool:
    """
    Concatenate specific fields in a fixed order,
    then compare HMAC-SHA512 with Paymob's hmac value.
    """
    hmac_fields = [
        'amount_cents', 'created_at', 'currency', 'error_occured',
        'has_parent_transaction', 'id', 'integration_id', 'is_3d_secure',
        'is_auth', 'is_capture', 'is_refunded', 'is_standalone_payment',
        'is_voided', 'order', 'owner', 'pending',
        'source_data_pan', 'source_data_sub_type', 'source_data_type',
        'success',
    ]
    concatenated = ''.join(str(data.get(field, '')) for field in hmac_fields)
    expected = hmac.new(
        settings.PAYMOB_HMAC_SECRET.encode(),
        concatenated.encode(),
        hashlib.sha512,
    ).hexdigest()
    return hmac.compare_digest(expected, data.get('hmac', ''))