from django import template

register = template.Library()

@register.filter
def sub(value, arg):
    return value - arg

@register.filter
def percentage(value):
    return (value / 20) * 100

