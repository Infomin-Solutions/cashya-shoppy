import json
import requests
import razorpay
from django.utils import timezone
from rest_framework.serializers import ValidationError
from phonepe.sdk.pg.env import Env
from phonepe.sdk.pg.payments.v1.models.request.pg_pay_request import PgPayRequest
from phonepe.sdk.pg.payments.v1.payment_client import PhonePePaymentClient
from paytmpg import MerchantProperty, Payment, PaymentDetailsBuilder, LibraryConstants, EChannelId, Money, EnumCurrency, UserInfo
from paytmchecksum import PaytmChecksum

phonepe_client = PhonePePaymentClient(
    merchant_id='PGTESTPAYUAT86',
    salt_key='96434309-7796-489d-8924-ab56988a6076',
    salt_index=1,
    env=Env.UAT
)
razorpay_client = razorpay.Client(
    auth=('rzp_test_U2QTSmNxrqTbil', 'TpoYjvZXQICO9fTSxXx6H6hp'))
razorpay_client.set_app_details({"title": "Test App", "version": "1"})
paytm_mid = 'micoUt79147315503216'
paytm_secret = '5#0L4Fmws9p7gy&b'
paytm_website = 'WEBSTAGING'
paytm_environment = 'https://securegw-stage.paytm.in'
MerchantProperty.initialize(
    LibraryConstants.STAGING_ENVIRONMENT, 'micoUt79147315503216', '5#0L4Fmws9p7gy&b', 'C3', 'DEFAULT')
MerchantProperty.set_callback_url("https://shop.askjhansi.com/paytm/callback")


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


PAYMENT_MODES = [
    ('cod', 'Cash on delivery'),
    ('razorpay', 'Online payment (Razorpay)'),
    ('phonepe', 'Online payment (PhonePe)'),
    ('paytm', 'Online payment (Paytm)'),
]


def get_phonepe_config(order_id, amount, user_id):
    order_id = str(order_id)
    amount = int(float(amount) * 100)
    user_id = str(user_id)
    callback_url = f"http://127.0.0.1:3000/phonepe/callback/{order_id}"
    pay_page_request = PgPayRequest.pay_page_pay_request_builder(
        merchant_order_id=order_id,
        merchant_transaction_id=order_id,
        merchant_user_id='USER_1',
        amount=amount,
        # callback_url='callback_url',
        redirect_url=callback_url,
        redirect_mode='REDIRECT',
    )
    pay_page_response = phonepe_client.pay(pay_page_request)
    return {
        'config': {
            'txn_token': pay_page_response.data.instrument_response.redirect_info.url,
            'callback_url': callback_url
        },
        'order_id': pay_page_response.data.transaction_id or pay_page_response.data.merchant_transaction_id,
        'status': pay_page_response.code
    }


def get_razorpay_config(order_id, amount, name, phone):
    order = razorpay_client.order.create(data={
        "amount": amount,
        "currency": "INR",
        "receipt": order_id,
    })
    config = {
        "key": razorpay_client.auth[0],
        "name": "Test App",
        "description": "Test Transaction",
        "image": "https://www.askjhansi.com/logo.png",
        "order_id": order.get('id'),
        "callback_url": f"http://127.0.0.1:3000/razorpay/callback/{order_id}",
        "prefill": {
            "name": name,
            "contact": phone
        },
        "theme": {
            "color": "#3399cc"
        }
    }
    return {
        'config': config,
        'order_id': order.get('id'),
        'status': order.get('status')
    }


# def get_paytm_config(order_id, amount, user_id, name, phone):
#     user_info = UserInfo()
#     user_info.set_cust_id(user_id)
#     user_info.set_first_name(name)
#     user_info.set_mobile(phone)

#     payment_details = PaymentDetailsBuilder(
#         EChannelId.WEB,
#         order_id,
#         Money(EnumCurrency.INR, str(float(amount))),
#         user_info
#     ).build()
#     response: dict = json.loads(Payment.createTxnToken(
#         payment_details).get_json_response().decode('utf-8'))
#     txn_token = ''
#     status = response.get('body', {}).get(
#         'resultInfo', {}).get('resultStatus', 'F')
#     if status == 'S':
#         txn_token = response.get('body').get('txnToken')
#     return {
#         'config': f"{MerchantProperty.base_url}/merchantpgpui/checkoutjs/merchants/{MerchantProperty.get_mid()}.js",
#         'order_id': txn_token,
#         'status': status
#     }


def get_paytm_config(order_id, amount, user_id, name, phone):
    paytmParams = dict()
    paytmParams["body"] = {
        "requestType": "Payment",
        "mid": paytm_mid,
        "websiteName": paytm_website,
        "orderId": order_id,
        "callbackUrl": f"http://127.0.0.1:3000/paytm/callback/{order_id}",
        "txnAmount": {
            "value": str(round(float(amount), 2)),
            "currency": "INR",
        },
        "userInfo": {
            "custId": f"CUST{user_id}",
            "mobile": phone,
            "firstName": name
        },
    }
    checksum = PaytmChecksum.generateSignature(
        json.dumps(paytmParams["body"]), paytm_secret)
    paytmParams["head"] = {
        "signature": checksum
    }
    post_data = json.dumps(paytmParams)
    url = f"{paytm_environment}/theia/api/v1/initiateTransaction?mid={paytm_mid}&orderId={order_id}"
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
        'config': f"{paytm_environment}/merchantpgpui/checkoutjs/merchants/{paytm_mid}.js",
        'order_id': token,
        'status': res["body"]["resultInfo"]["resultStatus"]
    }
