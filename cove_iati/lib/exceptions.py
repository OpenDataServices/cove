import json


class RuleSetStepException(Exception):
    def __init__(self, context, message=''):
        self.message = message
        try:
            self.id = context.xml.xpath('iati-identifier/text()')[0]
        except:
            pass

    def __str__(self):
        return json.dumps({
            'message': self.message,
            'id': self.id
        })
