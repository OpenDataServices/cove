from cove.lib.command_base import CoveCommandBase
import json
from cove.lib.tools import get_file_type
from cove_ocds.lib.schema import SchemaOCDS
from cove.lib.converters import convert_spreadsheet, convert_json
import os

class Command(CoveCommandBase):
    help = 'Run Command Line version of Cove OCDS'

    def add_arguments(self, parser):
        super().add_arguments(parser)
        parser.add_argument('--schema-version', default='', help='Version of schema to be used (only for OCDS)')

    def handle(self, file, *args, **options):
        super().handle(file, *args, **options)

        file_type = get_file_type(file)
        
