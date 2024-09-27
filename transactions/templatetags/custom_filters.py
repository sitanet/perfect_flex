from django import template

register = template.Library()

@register.filter
def starts_with(value, arg):
    """
    Check if value starts with a given prefix.
    """
    return value.startswith(arg)
