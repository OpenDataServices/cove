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

    def handle(self, files, *args, **options):
        super(Command, self).handle(files, *args, **options)
        stream = options.get('stream')
        openag = options.get('openag')
        orgids = options.get('orgids')

        if stream:
            for file in files:
                if os.path.isdir(file):
                    self.stderr.write('Skipping %s directory ' % str(file))
                else:
                    try:
                        result = iati_json_output(self.output_dir, file, openag=openag,
                                                  orgids=orgids)
                        result.update({'file': file})
                        self.stdout.write(json.dumps(result, cls=SetEncoder))
                    except APIException as e:
                        self.stdout.write(json.dumps({'file': file, 'error': e}))
                    except CoveInputDataError as e:
                        self.stdout.write(json.dumps({'file': file, 'error': 'Not well formed XML: %s'
                                                                             % str(e.context['error'])}))
        else:
            try:
                result = iati_json_output(self.output_dir, files[0], openag=openag, orgids=orgids)
                with open(os.path.join(self.output_dir, "results.json"), 'w+') as result_file:
                    json.dump(result, result_file, indent=2, cls=SetEncoder)
            except APIException as e:
                self.stderr.write(str(e))
                sys.exit(1)
            except CoveInputDataError as e:
                self.stderr.write('Not well formed XML: %s' % str(e.context['error']))
                sys.exit(1)
