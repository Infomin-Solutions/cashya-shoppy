import json
import os
import requests
import razorpay
import hashlib
import hmac
import base64
from django.utils import timezone
from rest_framework.serializers import ValidationError
from phonepe.sdk.pg.env import Env
from phonepe.sdk.pg.payments.v1.models.request.pg_pay_request import PgPayRequest
from phonepe.sdk.pg.payments.v1.payment_client import PhonePePaymentClient
from paytmchecksum import PaytmChecksum
from functools import wraps
from datetime import datetime
from django.conf import settings


def validate_coupon(cart, coupon=None):
    if not coupon:
        if cart.coupon:
            coupon = cart.coupon
        else:
            raise ValidationError('Invalid coupon')
    if not coupon.active or (coupon.quantity and coupon.quantity <= 0):
        raise ValidationError('Coupon is not available')
    if coupon.valid_from and coupon.valid_from > timezone.now():
        raise ValidationError('Coupon is not available yet')
    if coupon.valid_to and coupon.valid_to < timezone.now():
        raise ValidationError('Coupon has expired')
    if coupon.minimum_order_value and cart.sub_total < coupon.minimum_order_value:
        raise ValidationError(
            f"Minimum order value should be {coupon.minimum_order_value}")
    return coupon.code


def calculate_discount(cart):
    try:
        if cart.coupon and validate_coupon(cart):
            if cart.coupon.coupon_type == 'percentage':
                return round(cart.sub_total * cart.coupon.discount / 100, 2)
            return round(
                cart.coupon.discount if cart.sub_total - cart.coupon.discount > 0 else 1, 2)
        return 0
    except ValidationError:
        return 0


def calculate_payment_fee(order_amount):
    pg_charge = 2 / 100  # 2% payment gateway charge
    fee_multiplier = 1 - pg_charge
    total_amount = order_amount / fee_multiplier
    return round(total_amount - order_amount, 2)


def calculate_shipping(cart):
    return 0


def calculate_tax(cart):
    return 0


def calculate_total(cart):
    return round(cart.sub_total - calculate_discount(cart) + calculate_shipping(cart) + calculate_tax(cart), 2)


def requires(*fields):
    def decorator(fn):
        @wraps(fn)
        def wrapper(self, *args, **kwargs):
            for field in fields:
                if not hasattr(self, field):
                    raise AttributeError(f'{field} is required')
            return fn(self, *args, **kwargs)
        return wrapper
    return decorator


def timestamp(): return str(int(datetime.now().timestamp()))


def get_available_payment_modes():
    """Get payment modes filtered by admin settings and key availability."""
    from root.models import SiteSetting  # Import here to avoid circular imports

    available = []

    # Get admin settings (using get_or_create for the existing SiteSetting model)
    settings_obj, created = SiteSetting.objects.get_or_create(pk=1)

    # COD: check admin flag
    if settings_obj.enable_cod:
        available.append(('cod', 'Cash on delivery'))

    # PhonePe: check admin flag and keys
    if (settings_obj.enable_phonepe and
            os.getenv('PHONEPE_MERCHANT_ID')):
        available.append(('phonepe', 'Online payment (PhonePe)'))

    # Razorpay: check admin flag and keys
    if (settings_obj.enable_razorpay and
            os.getenv('RAZORPAY_API_KEY')):
        available.append(('razorpay', 'Online payment (Razorpay)'))

    # Paytm: check admin flag and keys
    if (settings_obj.enable_paytm and
            os.getenv('PAYTM_MID')):
        available.append(('paytm', 'Online payment (Paytm)'))

    return available


class PaymentGateway:
    STAGING = os.getenv('PG_STAGING', '1') == '1'

    class PhonePe:
        _MID = os.getenv('PHONEPE_MERCHANT_ID', '')
        __SALT_KEY = os.getenv('PHONEPE_SALT_KEY', '')
        _SALT_INDEX = int(os.getenv('PHONEPE_SALT_INDEX', '1'))
        _ENV_UAT = Env.UAT
        _ENV_PROD = Env.PROD

        @classmethod
        def _client(cls):
            return PhonePePaymentClient(
                merchant_id=cls._MID,
                salt_key=cls.__SALT_KEY,
                salt_index=cls._SALT_INDEX,
                env=cls._ENV_UAT if PaymentGateway.STAGING else cls._ENV_PROD,
            )

        order_id: str
        amount: str
        user_id: str

        def __init__(self, **kwars):
            for key, value in kwars.items():
                setattr(self, key, value)

        @requires('order_id', 'amount', 'user_id')
        def initiate_transaction(self):
            order_id = f"{self.order_id}X{timestamp()}"
            amount = int(float(self.amount) * 100)
            user_id = f"CUST{self.user_id}"
            callback_url = f"{settings.BE_SITE}/ecom/callback?pg=phonepe&transaction_id={order_id}"
            pay_page_request = PgPayRequest.pay_page_pay_request_builder(
                merchant_order_id=order_id,
                merchant_transaction_id=order_id,
                merchant_user_id=user_id,
                amount=amount,
                # callback_url='callback_url',
                redirect_url=callback_url,
                redirect_mode='REDIRECT',
            )
            pay_page_response = self._client().pay(pay_page_request)
            return {
                'txn_token': pay_page_response.data.instrument_response.redirect_info.url,
                'callback_url': callback_url,
                'order_id': order_id,
                'status': pay_page_response.code
            }

        @requires('order_id')
        def get_transaction_status(self):
            response = self._client().check_status(self.order_id)
            return {
                'paid': response.code == 'PAYMENT_SUCCESS',
                'status': response.code,
                # PAYMENT_SUCCESS, PAYMENT_PENDING, PAYMENT_DECLINED, PAYMENT_ERROR, TIMED_OUT, INTERNAL_SERVER_ERROR
                'order_id': response.data.merchant_transaction_id,
            }

        @classmethod
        def verify_callback_signature(cls, x_verify_header, response_body):
            """Verify PhonePe callback signature using X-VERIFY header"""
            if not x_verify_header:
                return False

            try:
                # X-VERIFY header format: "checksum###salt_index"
                checksum, salt_index = x_verify_header.split('###')

                # Verify salt index matches
                if int(salt_index) != cls._SALT_INDEX:
                    return False

                # Calculate expected checksum
                # PhonePe uses: base64(sha256(response_body + salt_key))
                calculated_checksum = base64.b64encode(
                    hashlib.sha256(
                        (response_body + cls.__SALT_KEY).encode()).digest()
                ).decode()

                return hmac.compare_digest(checksum, calculated_checksum)
            except (ValueError, IndexError, TypeError):
                return False

    class RazorPay:
        _API_KEY = os.getenv('RAZORPAY_API_KEY', '')
        __API_SECRET = os.getenv('RAZORPAY_API_SECRET', '')

        @classmethod
        def _client(cls):
            client = razorpay.Client(
                auth=(cls._API_KEY, cls.__API_SECRET)
            )
            client.set_app_details({"title": "Cashya Backend", "version": "1"})
            return client

        order_id: str
        amount: str
        name: str
        phone: str

        def __init__(self, **kwars):
            for key, value in kwars.items():
                setattr(self, key, value)

        @requires('order_id', 'amount', 'name', 'phone')
        def get_config(self):
            return {
                "key": self._API_KEY,
                "amount": int(float(self.amount) * 100),
                "currency": "INR",
                "name": "Test App",
                "description": "Test Transaction",
                "image": "https://www.askjhansi.com/logo.png",
                "order_id": self.order_id,
                "callback_url": f"{settings.BE_SITE}/ecom/callback?pg=razorpay&transaction_id={self.order_id}",
                "prefill": {
                    "name": self.name,
                    "contact": self.phone
                },
                "theme": {
                    "color": "#3399cc"
                }
            }

        @requires('order_id', 'amount', 'name', 'phone')
        def initiate_transaction(self):
            order = self._client().order.create(data={
                "amount": int(float(self.amount) * 100),
                "currency": "INR",
                "receipt": str(self.order_id),
            })
            return {
                'order_id': order.get('id'),
                'status': order.get('status')
            }

        @requires('order_id')
        def get_transaction_status(self):
            data = self._client().order.fetch(self.order_id)
            return {
                'paid': data.get('status') == 'paid',
                'status': data.get('status'),  # created, attempted, paid
                'order_id': data.get('receipt'),
            }

        @classmethod
        def verify_callback_signature(cls, razorpay_signature, payload_body, webhook_secret=None):
            """Verify Razorpay webhook signature"""
            if not razorpay_signature or not payload_body:
                return False

            try:
                # Use webhook secret if provided, otherwise use API secret
                secret = webhook_secret or cls.__API_SECRET

                # Calculate expected signature
                expected_signature = hmac.new(
                    secret.encode(),
                    payload_body.encode(),
                    hashlib.sha256
                ).hexdigest()

                return hmac.compare_digest(razorpay_signature, expected_signature)
            except (TypeError, AttributeError):
                return False

    class PayTm:
        _MID = os.getenv('PAYTM_MID', '')
        __SECRET = os.getenv('PAYTM_SECRET', '')
        _WEBSITE_UAT = 'WEBSTAGING'
        _WEBSITE_PROD = 'DEFAULT'
        _ENV_UAT = 'https://securegw-stage.paytm.in'
        _ENV_PROD = 'https://securegw.paytm.in'

        @classmethod
        def _get_conf(cls):
            staging = PaymentGateway.STAGING
            return {
                'mid': cls._MID,
                'secret': cls.__SECRET,
                'website': cls._WEBSITE_UAT if staging else cls._WEBSITE_PROD,
                'env_url': cls._ENV_UAT if staging else cls._ENV_PROD,
            }

        order_id: str
        amount: str
        user_id: str
        name: str
        phone: str

        def __init__(self, **kwars):
            for key, value in kwars.items():
                setattr(self, key, value)

        @requires('order_id', 'amount', 'user_id', 'name', 'phone')
        def initiate_transaction(self):
            paytmParams = dict()
            order_id = f"{self.order_id}X{timestamp()}"
            cfg = self._get_conf()
            paytmParams["body"] = {
                "requestType": "Payment",
                "mid": cfg['mid'],
                "websiteName": cfg['website'],
                "orderId": order_id,
                "callbackUrl": f"{settings.BE_SITE}/ecom/callback?pg=paytm&transaction_id={order_id}",
                "txnAmount": {
                    "value": str(round(float(self.amount), 2)),
                    "currency": "INR",
                },
                "userInfo": {
                    "custId": f"CUST{self.user_id}",
                    "mobile": self.phone,
                    "firstName": self.name
                },
            }
            checksum = PaytmChecksum.generateSignature(
                json.dumps(paytmParams["body"]), cfg['secret'])
            paytmParams["head"] = {
                "signature": checksum
            }
            post_data = json.dumps(paytmParams)
            url = f"{cfg['env_url']}/theia/api/v1/initiateTransaction?mid={cfg['mid']}&orderId={order_id}"
            response = requests.post(
                url,
                data=post_data,
                headers={
                    "Content-type": "application/json"
                }
            ).json()
            response_str = json.dumps(response)
            res = json.loads(response_str)
            if res["body"]["resultInfo"]["resultStatus"] == 'S':
                token = str(res["body"]["txnToken"])
            else:
                token = ''
                print(res)
            return {
                'config': f"{cfg['env_url']}/merchantpgpui/checkoutjs/merchants/{cfg['mid']}.js",
                'txn_token': token,
                'order_id': order_id,
                'status': res["body"]["resultInfo"]["resultStatus"]
            }

        @requires('order_id')
        def get_transaction_status(self):
            paytmParams = dict()
            cfg = self._get_conf()
            paytmParams["body"] = {
                'mid': cfg['mid'],
                'orderId': self.order_id
            }
            checksum = PaytmChecksum.generateSignature(
                json.dumps(paytmParams["body"]), cfg['secret'])
            paytmParams["head"] = {
                "signature": checksum
            }
            post_data = json.dumps(paytmParams)

            url = f"{cfg['env_url']}/v3/order/status"
            response = requests.post(
                url,
                data=post_data,
                headers={
                    "Content-type": "application/json"
                }
            ).json()
            response_str = json.dumps(response)
            res = json.loads(response_str)
            return {
                'paid': res["body"]["resultInfo"]["resultStatus"] == 'TXN_SUCCESS',
                'status': res["body"]["resultInfo"]["resultStatus"],
                # TXN_SUCCESS, TXN_FAILURE, PENDING, NO_RECORD_FOUND
                'order_id': res["body"]["orderId"]
            }

        @classmethod
        def verify_callback_signature(cls, checksum_header, payload_body):
            """Verify Paytm callback signature using checksum"""
            if not checksum_header or not payload_body:
                return False

            try:
                # Parse the payload as JSON to get parameters
                payload_data = json.loads(payload_body)

                # Paytm sends parameters in the request body
                # We need to verify the checksum using PaytmChecksum
                is_valid = PaytmChecksum.verifySignature(
                    payload_data,
                    cls.__SECRET,
                    checksum_header
                )
                return is_valid
            except (json.JSONDecodeError, TypeError, KeyError):
                return False
