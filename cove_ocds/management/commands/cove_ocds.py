import json
import os
import shutil
import sys

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from cove.lib.api import APIException
from cove_ocds.lib.ocds import cli_json_output


class SetEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, set):
            return list(obj)
        return json.JSONEncoder.default(self, obj)


class Command(BaseCommand):
    help = 'Run Command Line version of Cove OCDS'

    def add_arguments(self, parser):
        parser.add_argument('file', help='File to be processed by Cove')
        parser.add_argument('--output-dir', '-o', default='', help='Directory where the output is created, defaults to the name of the file')
        parser.add_argument('--delete', '-d', action='store_true', help='Delete existing directory if it exits')
        parser.add_argument('--exclude-file', '-e', action='store_true', help='Do not include the file in the output directory')
        parser.add_argument('--schema-version', '-s', default='', help='Version of the schema to validate the data')
        parser.add_argument('--convert', '-c', action='store_true', help='Convert data from nested (json) to flat format (spreadsheet) or vice versa')

    def handle(self, file, *args, **options):
        delete = options.get('delete')
        output_dir = options.get('output_dir')
        exclude_file = options.get('exclude_file')
        convert = options.get('convert')
        schema_version = options.get('schema_version')

        version_choices = settings.COVE_CONFIG['schema_version_choices']
        if schema_version and schema_version not in version_choices:
            raise CommandError('Value for schema version option is not valid. Accepted values: {}'.format(
                str(list(version_choices.keys()))
            ))

        if not output_dir:
            output_dir = file.split('/')[-1].split('.')[0]

        if os.path.exists(output_dir):
            if delete:
                shutil.rmtree(output_dir)
            else:
                self.stdout.write('Directory {} already exists'.format(output_dir))
                sys.exit(1)
        os.makedirs(output_dir)

        try:
            result = cli_json_output(output_dir, file, schema_version, convert)
        except APIException as e:
            self.stdout.write(str(e))
            sys.exit(1)

        with open(os.path.join(output_dir, "results.json"), 'w+') as result_file:
            json.dump(result, result_file, indent=2, cls=SetEncoder)

        if not exclude_file:
            shutil.copy2(file, output_dir)
