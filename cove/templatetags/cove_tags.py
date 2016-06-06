from django import template
import json

register = template.Library()


@register.inclusion_tag('modal_list.html')
def cove_modal_list(**kw):
    return kw


@register.inclusion_tag('modal_errors.html')
def cove_modal_errors(**kw):
    return kw


@register.filter(name='get_message')
def get_message(error):
    return json.loads(error)[1]


@register.filter(name='get_message_type')
def get_message_type(error):
    return json.loads(error)[0]


@register.filter(name='concat')
def concat(arg1, arg2):
    return str(arg1) + str(arg2)
