import requests
import pyotp
import qrcode
import base64
import time
from io import BytesIO
from django.conf import settings


def recaptcha_verify(token: str):
    try:
        response = requests.post(
            'https://www.google.com/recaptcha/api/siteverify',
            {
                'secret': settings.RECAPTCHA_SECRET_KEY,
                'response': token
            }
        )
        result = response.json()
        return result.get('success', False)
    except:
        return False


class TOTPManager:
    """TOTP Manager for handling 4-digit TOTP codes"""

    def __init__(self):
        plain_secret = settings.TOTP_SECRET
        self.secret = base64.b32encode(
            plain_secret.encode('utf-8')).decode('utf-8')
        self.totp = pyotp.TOTP(self.secret)

    def generate_4_digit_code(self):
        six_digit_code = self.totp.now()
        four_digit_code = six_digit_code[:4]
        return four_digit_code

    def verify_4_digit_code(self, user_code, window=1):
        if len(user_code) != 4 or not user_code.isdigit():
            return False

        current_time = int(time.time())

        for i in range(-window, window + 1):
            window_time = current_time + (i * 30)
            six_digit_code = self.totp.at(window_time)
            if six_digit_code[:4] == user_code:
                return True
        return False

    def get_provisioning_uri(self, account_name=None):
        account_name = account_name or settings.TOTP_ACCOUNT_NAME
        return self.totp.provisioning_uri(
            name=account_name,
            issuer_name=settings.TOTP_ISSUER_NAME
        )

    def generate_qr_code(self, account_name=None):
        uri = self.get_provisioning_uri(account_name)

        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(uri)
        qr.make(fit=True)
        qr.print_ascii(out=None, tty=False, invert=False)

        img = qr.make_image(fill_color="black", back_color="white")

        # Convert to bytes
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)

        return buffer.getvalue()

    def get_current_time_remaining(self):
        """Get remaining seconds in current time window"""
        return 30 - (int(time.time()) % 30)


# Global instance
totp_manager = TOTPManager()
