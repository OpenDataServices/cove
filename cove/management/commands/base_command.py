import json
import os
import shutil
import sys
import glob

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
        parser.add_argument('files', help='Files to be processed by Cove', nargs='+')
        parser.add_argument('--output-dir', '-o', default='', help='Directory where the output is created, defaults to the name of the file')
        parser.add_argument('--delete', '-d', action='store_true', help='Delete existing directory if it exits')
        parser.add_argument('--exclude-file', '-e', action='store_true', help='Do not include the file in the output directory')
        parser.add_argument('--stream', '-st', action='store_true', help='Do not include the file in the output directory')

    def handle(self, files, *args, **options):

        stream = options.get('stream')
        if (len(files) > 1 or len(glob.glob(files[0])) > 1 or os.path.isdir(glob.glob(files[0])[0])) and not stream:
            self.stdout.write('The multiple file option must be used with the --stream option')
            sys.exit(1)

        output_dir = options.get('output_dir')
        delete = options.get('delete')
        exclude_file = options.get('exclude_file')

        if not stream:
            file = files[0]
            if not output_dir:
                output_dir = file.split('/')[-1].split('.')[0]

            if os.path.exists(output_dir):
                if delete:
                    shutil.rmtree(output_dir)
                else:
                    self.stdout.write('Directory {} already exists'.format(output_dir))
                    sys.exit(1)
            os.makedirs(output_dir)

            if not exclude_file or stream:
                shutil.copy2(file, output_dir)

            self.output_dir = output_dir
