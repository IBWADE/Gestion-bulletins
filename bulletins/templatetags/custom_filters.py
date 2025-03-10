from django import template
from datetime import datetime

register = template.Library()

@register.filter
def month_name(month_number):
    return datetime(2023, month_number, 1).strftime('%B')  # Retourne le nom complet du mois