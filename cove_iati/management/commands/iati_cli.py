import json
import os
import sys


from cove.lib.exceptions import CoveInputDataError
from cove.management.commands.base_command import CoveBaseCommand, SetEncoder
from cove_iati.lib.api import APIException, iati_json_output


class Command(CoveBaseCommand):
    help = 'Run Command Line version of Cove IATI'

    def add_arguments(self, parser):
        parser.add_argument('--openag', '-a', action='store_true', help='Run ruleset checks for IATI OpenAg')
        parser.add_argument('--orgids', '-i', action='store_true', help='Check IATI identifier prefixes against '
                            'Org-ids prefixes')
        super(Command, self).add_arguments(parser)

    def handle(self, file, *args, **options):
        super(Command, self).handle(file, *args, **options)
        openag = options.get('openag')
        orgids = options.get('orgids')

        try:
            result = iati_json_output(self.output_dir, file, openag=openag, orgids=orgids)
        except APIException as e:
            self.stdout.write(str(e))
            sys.exit(1)
        except CoveInputDataError as e:
            self.stdout.write('Not well formed XML: %s' % str(e.context['error']))
            sys.exit(1)

        with open(os.path.join(self.output_dir, "results.json"), 'w+') as result_file:
            json.dump(result, result_file, indent=2, cls=SetEncoder)
