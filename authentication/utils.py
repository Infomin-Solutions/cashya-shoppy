import requests
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
