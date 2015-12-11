from django import template

register = template.Library()


@register.inclusion_tag('modal_list.html')
def cove_modal_list(**kw):
    return kw
