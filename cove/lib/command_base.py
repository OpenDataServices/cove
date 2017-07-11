from django.core.management.base import BaseCommand
import os
import sys


class CoveCommandBase(BaseCommand):
    help = 'Run Command Line version of Cove'

    def add_arguments(self, parser):
        parser.add_argument('file', help='File Cove to process.')
        parser.add_argument('--output-dir', default='', help='Directory where output is created, defaults to the name of the file')

    def handle(self, file, *args, **options):
        output_dir = options.get("output_dir")
        if not output_dir:
            output_dir = file.split('/')[-1].split('.')[0]

        try:
            os.makedirs(output_dir)
        except OSError:
            self.stdout.write("Directory {} already exists".format(output_dir))
            sys.exit(1)

        self.output_dir = output_dir
