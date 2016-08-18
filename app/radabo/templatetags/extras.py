from django import template
from operator import itemgetter
register = template.Library()

@register.filter
def sort_by(data, order):
    return sorted(data, key=itemgetter(order))
