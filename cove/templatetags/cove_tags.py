from django import template
import random
import json

register = template.Library()


@register.inclusion_tag('modal_list.html')
def cove_modal_list(**kw):
    return kw


@register.inclusion_tag('modal_errors.html')
def cove_modal_errors(**kw):
    return kw


@register.filter(name='json_decode')
def json_decode(error_json):
    return json.loads(error_json)


@register.filter(name='concat')
def concat(arg1, arg2):
    return str(arg1) + str(arg2)


@register.filter
def subtract(value, arg):
    return value - arg


@register.filter(name='sample')
def sample(population, k):
    return random.sample(population, k)
