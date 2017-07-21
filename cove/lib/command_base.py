from django.core.management.base import BaseCommand
import os
import sys
import shutil


class CoveCommandBase(BaseCommand):
    help = 'Run Command Line version of Cove'

    def add_arguments(self, parser):
        parser.add_argument('file', help='File to be processed by Cove')
        parser.add_argument('--output-dir', '-o', default='', help='Directory where output is created, defaults to the name of the file')
        parser.add_argument('--delete', '-d', action='store_true', help='Delete existing directory if it exits')
        parser.add_argument('--exclude-file', '-e', action='store_true', help='Do not include the file in the output directory')

    def handle(self, file, *args, **options):
        output_dir = options.get('output_dir')
        exclude_file = options.get('exclude_file')

        if not output_dir:
            output_dir = file.split('/')[-1].split('.')[0]

        if os.path.exists(output_dir):
            if options['delete']:
                shutil.rmtree(output_dir)
            else:
                self.stdout.write('Directory {} already exists'.format(output_dir))
                sys.exit(1)

        os.makedirs(output_dir)
        self.output_dir = output_dir

        if not exclude_file:
            shutil.copy2(file, self.output_dir)
