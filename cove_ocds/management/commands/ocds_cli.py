import json
import os
import sys
import glob

from django.conf import settings
from django.core.management.base import CommandError

from cove.management.commands.base_command import CoveBaseCommand, SetEncoder
from cove_ocds.lib.api import APIException, ocds_json_output


class Command(CoveBaseCommand):
    help = 'Run Command Line version of Cove OCDS'

    def add_arguments(self, parser):
        parser.add_argument('--schema-version', '-s', default='', help='Version of the schema to validate the data')
        parser.add_argument('--convert', '-c', action='store_true',
                            help='Convert data from nested (json) to flat format (spreadsheet) or vice versa')
        super(Command, self).add_arguments(parser)

    def handle(self, files, *args, **options):
        super(Command, self).handle(files, *args, **options)

        convert = options.get('convert')
        stream = options.get('stream')
        schema_version = options.get('schema_version')
        version_choices = settings.COVE_CONFIG['schema_version_choices']

        if schema_version and schema_version not in version_choices:
            raise CommandError('Value for schema version option is not valid. Accepted values: {}'.format(
                str(list(version_choices.keys()))
            ))

        try:
            if stream:
                for file in files:
                    real_files = glob.glob(file)
                    for real_file in real_files:
                        if os.path.isdir(real_file):
                            self.stdout.write('Skipping %s directory ', real_file)
                        else:
                            result = ocds_json_output(self.output_dir, real_file, schema_version,
                                                      convert)
                            self.stdout.write(str(result))
            else:
                result = ocds_json_output(self.output_dir, files[0], schema_version, convert)
                with open(os.path.join(self.output_dir, 'results.json'), 'w+') as result_file:
                    json.dump(result, result_file, indent=2, cls=SetEncoder)
        except APIException as e:
            self.stdout.write(str(e))
            sys.exit(1)
