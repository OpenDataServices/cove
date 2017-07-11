from cove.lib.command_base import CoveCommandBase
import json
from cove.lib.tools import get_file_type
from cove_ocds.lib.schema import SchemaOCDS
from cove_ocds.views import common_checks_ocds
from cove.lib.common import get_spreadsheet_meta_data
from cove.lib.converters import convert_spreadsheet, convert_json
import pprint


class Command(CoveCommandBase):
    help = 'Run Command Line version of Cove OCDS'

    def add_arguments(self, parser):
        super().add_arguments(parser)
        parser.add_argument('--schema-version', default='', help='Version of schema to be used (only for OCDS)')

    def handle(self, file, *args, **options):
        super().handle(file, *args, **options)

        context = {}
        file_type = get_file_type(file)
        context = {"file_type": file_type}

        if file_type == 'json':
            with open(file, encoding='utf-8') as fp:
                try:
                    json_data = json.load(fp)
                except ValueError as err:
                    self.stdout.write('The file looks like invalid json')

                schema_ocds = SchemaOCDS(release_data=json_data)
                
                if schema_ocds.extensions:
                    schema_ocds.create_extended_release_schema_file(self.output_dir, "")

                url = schema_ocds.extended_schema_file or schema_ocds.release_schema_url

                context.update(convert_json(self.output_dir, '', file, schema_url=url, flatten=True))

        else:
            metatab_schema_url = SchemaOCDS(select_version='1.1').release_pkg_schema_url
            metatab_data = get_spreadsheet_meta_data(self.output_dir, file, metatab_schema_url, file_type=file_type)

            schema_ocds = SchemaOCDS(release_data=metatab_data)

            #if schema_ocds.invalid_version_data:
            #    raise_invalid_version_data(metatab_data.get('version'))

            # Replace json conversion when user chooses a different schema version.
            #if db_data.schema_version and schema_ocds.version != db_data.schema_version:
            #    replace = True

            if schema_ocds.extensions:
                schema_ocds.create_extended_release_schema_file(self.output_dir, '')
            url = schema_ocds.extended_schema_file or schema_ocds.release_schema_url
            pkg_url = schema_ocds.release_pkg_schema_url

            context.update(convert_spreadsheet(self.output_dir, '', file, file_type, schema_url=url, pkg_schema_url=pkg_url))

            with open(context['converted_path'], encoding='utf-8') as fp:
                json_data = json.load(fp)

        #if replace:
        #    if os.path.exists(validation_errors_path):
        #        os.remove(validation_errors_path)

        context = common_checks_ocds(context, self.output_dir, json_data, schema_ocds)

        pprint.pprint(context)
