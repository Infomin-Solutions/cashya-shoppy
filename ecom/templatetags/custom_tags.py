import json
import locale
from django import template

locale.setlocale(locale.LC_ALL, 'en_IN.utf8')
register = template.Library()


@register.filter
def comma(value: float) -> str:
    return locale.format_string("%.2f", value, grouping=True)
