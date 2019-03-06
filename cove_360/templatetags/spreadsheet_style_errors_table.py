from django import template
from collections import OrderedDict, defaultdict

register = template.Library()


@register.filter(name='spreadsheet_style_errors_table')
def spreadsheet_style_errors_table(examples):
    if not examples:
        return ''
    sheets = list(OrderedDict.fromkeys(example.get('sheet', '') for example in examples))

    out = {}

    example_cell_lookup = defaultdict(lambda: defaultdict(dict))
    for example in examples:
        example_cell_lookup[example.get('sheet', '')][example.get('col_alpha', '')][example.get('row_number', '')] = example.get('value', '')

    for sheet in sheets:
        col_alphas = list(OrderedDict.fromkeys(example.get('col_alpha', '') for example in examples if example.get('sheet', '') == sheet))
        row_numbers = list(OrderedDict.fromkeys(example.get('row_number', '') for example in examples if example.get('sheet', '') == sheet))
        out[sheet] = [[''] + col_alphas] + [[example.get('row_number', '')] + [example_cell_lookup.get(sheet, {}).get(col_alpha, {}).get(row_number, '') for col_alpha in col_alphas] for row_number in row_numbers]
    print(out.items())
    return out.items()
