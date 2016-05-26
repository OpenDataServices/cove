from django import template
import json

register = template.Library()


@register.inclusion_tag('modal_list.html')
def cove_modal_list(**kw):
    return kw


@register.filter(name='get_message')
def get_message(error):
    return json.loads(error)[1]
