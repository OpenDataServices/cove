import json


class RuleSetStepException(Exception):
    def __init__(self, context, errors=''):
        self.errors = errors
        self.id = ''
        self.feature_name = context.feature.name
        try:
            self.id = context.xml.xpath('iati-identifier/text()')[0]
        except IndexError:
            pass

    def __str__(self):
        return json.dumps({
            'errors': self.errors,
            'id': self.id,
            'ruleset': self.feature_name
        })
