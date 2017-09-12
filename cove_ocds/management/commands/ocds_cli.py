import json
import os
import sys

from django.conf import settings
from django.core.management.base import CommandError

from cove.management.commands.base_command import CoveBaseCommand, SetEncoder
from cove_ocds.lib.api import APIException, ocds_json_output


class Command(CoveBaseCommand):
    help = 'Run Command Line version of Cove OCDS'

    def add_arguments(self, parser):
        parser.add_argument('--schema-version', '-s', default='', help='Version of the schema to validate the data')
        parser.add_argument('--convert', '-c', action='store_true', help='Convert data from nested (json) to flat format (spreadsheet) or vice versa')
        super(Command, self).add_arguments(parser)

    def handle(self, file, *args, **options):
        super(Command, self).handle(file, *args, **options)

        convert = options.get('convert')
        schema_version = options.get('schema_version')
        version_choices = settings.COVE_CONFIG['schema_version_choices']

        if schema_version and schema_version not in version_choices:
            raise CommandError('Value for schema version option is not valid. Accepted values: {}'.format(
                str(list(version_choices.keys()))
            ))

        try:
            result = ocds_json_output(self.output_dir, file, schema_version, convert)
        except APIException as e:
            self.stdout.write(str(e))
            sys.exit(1)

        with open(os.path.join(self.output_dir, "results.json"), 'w+') as result_file:
            json.dump(result, result_file, indent=2, cls=SetEncoder)
