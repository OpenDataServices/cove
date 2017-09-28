import json
import os
import shutil
import sys

from django.core.management.base import BaseCommand


class SetEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, set):
            return list(obj)
        return json.JSONEncoder.default(self, obj)


class CoveBaseCommand(BaseCommand):
    def __init__(self, *args, **kwargs):
        self.output_dir = ''
        super(CoveBaseCommand, self).__init__(*args, **kwargs)

    def add_arguments(self, parser):
        parser.add_argument('file', help='File to be processed by Cove')
        parser.add_argument('--output-dir', '-o', default='', help='Directory where the output is created, defaults to the name of the file')
        parser.add_argument('--delete', '-d', action='store_true', help='Delete existing directory if it exits')
        parser.add_argument('--exclude-file', '-e', action='store_true', help='Do not include the file in the output directory')

    def handle(self, file, *args, **options):
        output_dir = options.get('output_dir')
        delete = options.get('delete')
        exclude_file = options.get('exclude_file')

        if not output_dir:
            output_dir = file.split('/')[-1].split('.')[0]

        if os.path.exists(output_dir):
            if delete:
                shutil.rmtree(output_dir)
            else:
                self.stdout.write('Directory {} already exists'.format(output_dir))
                sys.exit(1)
        os.makedirs(output_dir)

        if not exclude_file:
            shutil.copy2(file, output_dir)

        self.output_dir = output_dir
