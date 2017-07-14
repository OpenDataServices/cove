from django.core.management.base import BaseCommand
import os
import sys
import shutil


class CoveCommandBase(BaseCommand):
    help = 'Run Command Line version of Cove'

    def add_arguments(self, parser):
        parser.add_argument('file', help='File Cove to process.')
        parser.add_argument('--output-dir', '-o', default='', help='Directory where output is created, defaults to the name of the file')
        parser.add_argument('--delete', '-d', action='store_true', help='Delete existing directory if it exits')

    def handle(self, file, *args, **options):
        output_dir = options.get("output_dir")
        if not output_dir:
            output_dir = file.split('/')[-1].split('.')[0]

        if os.path.exists(output_dir):
            if options['delete']:
                shutil.rmtree(output_dir)
            else:
                self.stdout.write("Directory {} already exists".format(output_dir))
                sys.exit(1)

        os.makedirs(output_dir)

        self.output_dir = output_dir
