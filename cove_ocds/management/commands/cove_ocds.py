import json
import os
import sys
from shutil import copy2

from cove_ocds.lib.api import produce_json_output, APIException
from cove.lib.command_base import CoveCommandBase


class SetEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, set):
            return list(obj)
        return json.JSONEncoder.default(self, obj)


class Command(CoveCommandBase):
    help = 'Run Command Line version of Cove OCDS'

    def add_arguments(self, parser):
        super().add_arguments(parser)
        parser.add_argument('--schema-version', default='', help='Version of schema to be used')

    def handle(self, file, *args, **options):
        super().handle(file, *args, **options)
        exclude_file = options.get('exclude-file')

        try:
            result = produce_json_output(self.output_dir, file)
        except APIException as e:
            self.stdout.write(str(e))
            sys.exit(1)

        with open(os.path.join(self.output_dir, "results.json"), 'w+') as result_file:
            json.dump(result, result_file, indent=2, cls=SetEncoder)

        if not exclude_file:
            copy2(file, self.output_dir)
