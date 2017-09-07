import json
import os
import sys

from cove.management.commands.base_command import CoveBaseCommand, SetEncoder
from cove_iati.lib.api import APIException
from cove_iati.lib.iati import cli_json_output


class Command(CoveBaseCommand):
    help = 'Run Command Line version of Cove IATI'

    def handle(self, file, *args, **options):
        super(Command, self).handle(file, *args, **options)

        try:
            result = cli_json_output(self.output_dir, file)
        except APIException as e:
            self.stdout.write(str(e))
            sys.exit(1)

        with open(os.path.join(self.output_dir, "results.json"), 'w+') as result_file:
            json.dump(result, result_file, indent=2, cls=SetEncoder)
