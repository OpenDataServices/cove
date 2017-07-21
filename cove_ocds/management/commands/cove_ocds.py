import json
import os
import shutil
import sys

from django.core.management.base import BaseCommand

from cove_ocds.lib.api import produce_json_output, APIException


class SetEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, set):
            return list(obj)
        return json.JSONEncoder.default(self, obj)


class Command(BaseCommand):
    help = 'Run Command Line version of Cove OCDS'

    def add_arguments(self, parser):
        parser.add_argument('file', help='File to be processed by Cove')
        parser.add_argument('--output-dir', '-o', default='', help='Directory where output is created, defaults to the name of the file')
        parser.add_argument('--delete', '-d', action='store_true', help='Delete existing directory if it exits')
        parser.add_argument('--exclude-file', '-e', action='store_true', help='Do not include the file in the output directory')
        parser.add_argument('--schema-version', '-s', default='', help='Version of schema to be used')
        parser.add_argument('--convert', '-c', action='store_true', help='Convert data from nested (json) to flat format (spreadsheet)')

    def handle(self, file, *args, **options):
        delete = options.get('delete')
        output_dir = options.get('output_dir')
        exclude_file = options.get('exclude_file')
        schema_version = options.get('schema_version')
        convert = options.get('convert')

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
            result = produce_json_output(output_dir, file, schema_version, convert)
        except APIException as e:
            self.stdout.write(str(e))
            sys.exit(1)

        with open(os.path.join(output_dir, "results.json"), 'w+') as result_file:
            json.dump(result, result_file, indent=2, cls=SetEncoder)

        if not exclude_file:
            shutil.copy2(file, output_dir)
