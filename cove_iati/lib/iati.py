import json
import os
import re

import defusedxml.lxml as etree
import lxml.etree
import requests
from bdd_tester import bdd_tester
from django.utils.html import format_html
from django.utils.translation import ugettext_lazy as _
from libcove.lib.exceptions import CoveInputDataError
from libcove.lib.tools import ignore_errors

from cove_iati.lib.exceptions import UnrecognisedFileTypeXML
from cove_iati.lib.process_codelists import invalid_embedded_codelist_values, invalid_non_embedded_codelist_values
from .schema import SchemaIATI


def get_tree(data_file):
    with open(data_file, 'rb') as fp:
        try:
            tree = etree.parse(fp)
        except lxml.etree.XMLSyntaxError as err:
            raise CoveInputDataError(context={
                'sub_title': _("Sorry, we can't process that data"),
                'link': 'index',
                'link_text': _('Try Again'),
                'msg': _(format_html('We think you tried to upload a XML file, but it is not well formed XML.'
                         '\n\n<span class="glyphicon glyphicon-exclamation-sign" aria-hidden="true">'
                         '</span> <strong>Error message:</strong> {}', err)),
                'error': format(err)
            })
        except UnicodeDecodeError as err:
            raise CoveInputDataError(context={
                'sub_title': _("Sorry, we can't process that data"),
                'link': 'index',
                'link_text': _('Try Again'),
                'msg': _(format_html('We think you tried to upload a XML file, but the encoding is incorrect.'
                         '\n\n<span class="glyphicon glyphicon-exclamation-sign" aria-hidden="true">'
                         '</span> <strong>Error message:</strong> {}', err)),
                'error': format(err)
            })
        return tree


def common_checks_context_iati(context, upload_dir, data_file, file_type, tree, api=False, openag=False, orgids=False):
    '''TODO: this function is trying to do too many things. Separate some
    of its logic into smaller functions doing one single thing each.
    '''
    schema_iati = SchemaIATI()
    cell_source_map = {}
    validation_errors_path = os.path.join(upload_dir, 'validation_errors-3.json')

    if tree.getroot().tag == 'iati-organisations':
        schema_path = schema_iati.organisation_schema
        schema_name = 'Organisation'
        # rulesets don't support orgnisation files properly yet
        # so disable rather than give partial information
        ruleset_disabled = True
    else:
        schema_path = schema_iati.activity_schema
        schema_name = 'Activity'
        ruleset_disabled = False
    errors_all, invalid_data = validate_against_schema(schema_path, tree)

    return_on_error = [{'message': 'There was a problem running ruleset checks',
                        'exception': True}]

    # Validation errors
    if file_type != 'xml':
        with open(os.path.join(upload_dir, 'cell_source_map.json')) as cell_source_map_fp:
            cell_source_map = json.load(cell_source_map_fp)
    if os.path.exists(validation_errors_path):
        with open(validation_errors_path) as validation_error_fp:
            validation_errors = json.load(validation_error_fp)
    else:
        validation_errors = get_xml_validation_errors(errors_all, file_type, cell_source_map)
        if not api:
            with open(validation_errors_path, 'w+') as validation_error_fp:
                validation_error_fp.write(json.dumps(validation_errors))

    # Ruleset errors
    if ruleset_disabled:
        ruleset_errors = None
        org_ruleset_errors = None
    else:
        ruleset_errors = get_iati_ruleset_errors(
            tree,
            os.path.join(upload_dir, 'ruleset'),
            api=api,
            ignore_errors=invalid_data,
            return_on_error=return_on_error
        )
        org_ruleset_errors = get_iati_ruleset_errors(
            tree,
            os.path.join(upload_dir, 'ruleset_org_regex'),
            api=api,
            ignore_errors=invalid_data,
            return_on_error=return_on_error,
            feature_dir='cove_iati/rulesets/iati_org_regex_ruleset/'
        )

    if openag:
        ruleset_errors_ag = get_openag_ruleset_errors(
            tree,
            os.path.join(upload_dir, 'ruleset_openang'),
            ignore_errors=invalid_data,
            return_on_error=return_on_error
        )
        context.update({'ruleset_errors_openag': ruleset_errors_ag})
    if orgids:
        ruleset_errors_orgids = get_orgids_ruleset_errors(
            tree,
            os.path.join(upload_dir, 'ruleset_orgids'),
            ignore_errors=invalid_data,
            return_on_error=return_on_error
        )
        context.update({'ruleset_errors_orgids': ruleset_errors_orgids})

    context.update({
        'validation_errors': sorted(validation_errors.items()),
        'ruleset_errors': ruleset_errors,
        'org_ruleset_errors': org_ruleset_errors,
        'file_type': file_type,
        'invalid_embedded_codelist_values': invalid_embedded_codelist_values(
            schema_iati.schema_directory,
            data_file,
            os.path.join(upload_dir, 'cell_source_map.json') if file_type != 'xml' else None
        ),
        'invalid_non_embedded_codelist_values': invalid_non_embedded_codelist_values(
            schema_iati.schema_directory,
            data_file,
            os.path.join(upload_dir, 'cell_source_map.json') if file_type != 'xml' else None
        )
    })

    if not api:
        context.update({
            'validation_errors_count': sum(len(value) for value in validation_errors.values()),
            'cell_source_map': cell_source_map,
            'first_render': False,
            'schema_name': schema_name,
            'ruleset_disabled': ruleset_disabled
        })
        if ruleset_errors:
            ruleset_errors_by_activity = get_iati_ruleset_errors(
                tree,
                os.path.join(upload_dir, 'ruleset'),
                group_by='activity',
                ignore_errors=invalid_data,
                return_on_error=return_on_error
            )
            context['ruleset_errors'] = [ruleset_errors, ruleset_errors_by_activity]

        if org_ruleset_errors:
            org_ruleset_errors_by_activity = get_iati_ruleset_errors(
                tree,
                os.path.join(upload_dir, 'ruleset_org_regex'),
                group_by='activity',
                ignore_errors=invalid_data,
                return_on_error=return_on_error,
                feature_dir='cove_iati/rulesets/iati_org_regex_ruleset/'
            )
            context['org_ruleset_errors'] = [org_ruleset_errors, org_ruleset_errors_by_activity]

        count_ruleset_errors = 0
        if isinstance(ruleset_errors, dict):
            for rules in ruleset_errors.values():
                for errors in rules.values():
                    count_ruleset_errors += len(errors)

        context['ruleset_errors_count'] = count_ruleset_errors

        count_org_ruleset_errors = 0
        if isinstance(org_ruleset_errors, dict):
            for rules in org_ruleset_errors.values():
                for errors in rules.values():
                    count_org_ruleset_errors += len(errors)

        context['org_ruleset_errors_count'] = count_org_ruleset_errors

    return context


def validate_against_schema(schema_path, tree):
    with open(schema_path) as schema_fp:
        schema_tree = etree.parse(schema_fp)

    schema = lxml.etree.XMLSchema(schema_tree)
    schema.validate(tree)
    lxml_errors = lxml_errors_generator(schema.error_log)
    errors_all = format_lxml_errors(lxml_errors)
    invalid_data = bool(schema.error_log)
    return errors_all, invalid_data


def lxml_errors_generator(schema_error_log):
    '''Yield dict with lxml error path and message

    Be aware that lxml does not include path indexes for single item arrays.

    one activity in data:
        iati-activities/iati-activity/activity-date/@iso-date

    two activities in data:
        iati-activities/iati-activity[1]/activity-date/@iso-date
        iati-activities/iati-activity[2]/activity-date/@iso-date

    This causes a problem when matching lxml error paths and cell source paths
    as the latter does include an index position for sequences with a single array.
    '''
    for error in schema_error_log:
        yield {
            'path': error.path,
            'message': error.message,
            'line': error.line,
        }


def format_lxml_errors(lxml_errors):
    '''Convert lxml validation errors into structured errors'''
    for error in lxml_errors:
        # lxml uses path indexes starting from 1 in square brackets
        indexes = ['/{}'.format(str(int(i[1:-1]) - 1)) for i in re.findall(r'\[\d+\]', error['path'])]

        attribute = None
        attr_start = error['message'].find('attribute')
        if attr_start != -1:
            attribute = error['message'][attr_start + len("attribute '"):]
            attr_end = attribute.find("':")
            attribute = attribute[:attr_end]

        path = re.sub(r'\[\d+\]', '{}', error['path']).format(*indexes)
        path = re.sub(r'/iati-activities/', '', path)
        if attribute:
            path = '{}/@{}'.format(path, attribute)
        
        message = error['message']
        value = ''

        if 'element is not expected' in message or 'Missing child element' in message:
            message = message.replace('. Expected is (', ', expected is').replace(' )', '')
        elif 'required but missing' in message or 'content other than whitespace is not allowed' in message:
            pass
        else:
            val_start = error['message'].find(": '")
            value = error['message'][val_start + len(": '"):]
            val_end = value.find("'")
            value = value[:val_end]
        message = message.replace('Element ', '').replace(": '{}'".format(value), '')

        yield {
            'path': path,
            'message': message,
            'value': value,
            'line': error['line'],
        }


def get_zero_paths_list(cell_path):
    '''Get all combinations of zeroes removed/not removed in a cell source path

    Returns a list. The list doesn't include the original path.

    e.g:
        'path/0/to/1/cell/0/source' will produce:

        ['path/1/to/1/cell/0/source',
         'path/0/to/1/cell/1/source',
         'path/to/1/cell/source']
    '''
    cell_zero_indexes, cell_zero_combinations, zero_paths_list = [], [], []
    cell_path_chars = cell_path.split('/')

    for index, char in enumerate(cell_path_chars):
        if char == '0':
            cell_zero_indexes.append(index)

    n_zeros = len(cell_zero_indexes)
    for i in range(1, 2 ** n_zeros):
        cell_zero_combinations.append(bin(i)[2:].zfill(n_zeros))

    for bin_repr in cell_zero_combinations:
        for index_bit in zip(cell_zero_indexes, bin_repr):
            if index_bit[1] == '0':
                cell_path_chars[index_bit[0]] = '0'
            else:
                cell_path_chars[index_bit[0]] = None
        path = '/'.join(filter(bool, cell_path_chars))
        zero_paths_list.append(path)

    return zero_paths_list


def error_path_source(error, cell_source_paths, cell_source_map, missing_zeros=False):
    source = {}
    found_path = None

    if missing_zeros:
        for cell_path in cell_source_paths:
            if error['path'] in get_zero_paths_list(cell_path):
                found_path = cell_path
                break
    else:
        for cell_path in cell_source_paths:
            if cell_path == error['path']:
                found_path = cell_path
                break

    if found_path:
        if len(cell_source_map[cell_path][0]) > 2:
            source = {
                'sheet': cell_source_map[cell_path][0][0],
                "col_alpha": cell_source_map[cell_path][0][1],
                'row_number': cell_source_map[cell_path][0][2],
                'header': cell_source_map[cell_path][0][3],
                'path': cell_path,
                'value': error['value']
            }
        else:
            source = {
                'sheet': cell_source_map[cell_path][0][0],
                'row_number': cell_source_map[cell_path][0][1],
                'header': cell_path,
                'path': cell_path,
                'value': error['value']
            }
    return source


def get_xml_validation_errors(errors, file_type, cell_source_map):
    validation_errors = {}
    if file_type != 'xml':
        cell_source_map_paths = {}
        for cell_path in cell_source_map.keys():
            generic_cell_path = re.sub(r'/\d+', '', cell_path)
            if cell_source_map_paths.get(generic_cell_path):
                cell_source_map_paths[generic_cell_path].append(cell_path)
            else:
                cell_source_map_paths[generic_cell_path] = [cell_path]

    for error in errors:
        validation_key = json.dumps({'message': error['message']}, sort_keys=True)
        if not validation_errors.get(validation_key):
            validation_errors[validation_key] = []

        if file_type != 'xml':
            generic_error_path = re.sub(r'/\d+', '', error['path'])
            cell_paths = cell_source_map_paths.get(generic_error_path, [])
            source = error_path_source(error, cell_paths, cell_source_map)
            if not source:
                source = error_path_source(error, cell_paths, cell_source_map, missing_zeros=True)
        else:
            source = {'path': error['path'], 'value': error['value']}

        source.update({'line': error['line']})
        validation_errors[validation_key].append(source)

    return validation_errors


def format_ruleset_errors(output_dir):
    ruleset_errors = []

    for output_file in os.listdir(output_dir):
        with open(os.path.join(output_dir, output_file)) as fp:
            scenario_outline = ' '.join(re.sub('\.', '/', output_file[:-7]).split('_'))
            for line in fp:
                line = line.strip()

                if line:
                    json_line = json.loads(line)
                    for error in json_line['errors']:
                        rule_error = {
                            'id': json_line['id'],
                            'path': error['path'],
                            'rule': scenario_outline,
                            'explanation': error['explanation'],
                            'ruleset': json_line['ruleset']
                        }
                        ruleset_errors.append(rule_error)

    return ruleset_errors


def _ruleset_errors_by_rule(flat_errors):
    ruleset_errors = {}
    for error in flat_errors:
        if error['ruleset'] not in ruleset_errors:
            ruleset_errors[error['ruleset']] = {}
        if error['rule'] not in ruleset_errors[error['ruleset']]:
            ruleset_errors[error['ruleset']][error['rule']] = []
        ruleset_errors[error['ruleset']][error['rule']].append([
            error['id'], error['explanation'], error['path']
        ])
    return ruleset_errors


def _ruleset_errors_by_activity(flat_errors):
    ruleset_errors = {}
    for error in flat_errors:
        if error['id'] not in ruleset_errors:
            ruleset_errors[error['id']] = {}
        if error['ruleset'] not in ruleset_errors[error['id']]:
            ruleset_errors[error['id']][error['ruleset']] = []
        ruleset_errors[error['id']][error['ruleset']].append([
            error['rule'], error['explanation'], error['path']
        ])
    return ruleset_errors


@ignore_errors
def get_iati_ruleset_errors(lxml_etree, output_dir, group_by='rule', api=False,
                            feature_dir='cove_iati/rulesets/iati_standard_v2_ruleset/'):
    if group_by not in ['rule', 'activity']:
        raise ValueError('Only `rule` or `activity` are valid values for group_by argument')

    bdd_tester(etree=lxml_etree, features=[feature_dir],
               output_path=output_dir)

    if not os.path.isdir(output_dir):
        return []
    if api:
        return format_ruleset_errors(output_dir)
    if group_by == 'rule':
        return _ruleset_errors_by_rule(format_ruleset_errors(output_dir))
    else:
        return _ruleset_errors_by_activity(format_ruleset_errors(output_dir))


@ignore_errors
def get_openag_ruleset_errors(lxml_etree, output_dir):
    bdd_tester(etree=lxml_etree, features=['cove_iati/rulesets/iati_openag_ruleset/'],
               output_path=output_dir)

    if not os.path.isdir(output_dir):
        return []
    return format_ruleset_errors(output_dir)


@ignore_errors
def get_orgids_ruleset_errors(lxml_etree, output_dir):
    bdd_tester(etree=lxml_etree, features=['cove_iati/rulesets/iati_orgids_ruleset/'],
               output_path=output_dir)

    if not os.path.isdir(output_dir):
        return []
    return format_ruleset_errors(output_dir)


def get_file_type(file):
    if isinstance(file, str):
        name = file.lower()
    else:
        name = file.name.lower()
    if name.endswith('.xml'):
        return 'xml'
    elif name.endswith('.xlsx'):
        return 'xlsx'
    elif name.endswith('.ods'):
        return 'ods'
    elif name.endswith('.csv'):
        return 'csv'
    else:
        raise UnrecognisedFileTypeXML


def iati_identifier_count(tree):
    root = tree.getroot()
    identifiers = root.xpath('/iati-activities/iati-activity/iati-identifier/text()')
    unique_identifiers = list(set(identifiers))

    return len(unique_identifiers)


def organisation_identifier_count(tree):
    root = tree.getroot()
    identifiers = root.xpath('/iati-organisations/iati-organisation/organisation-identifier/text()')
    unique_identifiers = list(set(identifiers))

    return len(unique_identifiers)


ACTIVITY_PREFIX = '/iati-activities/iati-activity'


def check_activity_org_refs(tree):
    root = tree.getroot()
    
    publishers = requests.get("https://codelists.codeforiati.org/api/json/en/ReportingOrganisation.json").json()
    registration_agency = requests.get("https://codelists.codeforiati.org/api/json/en/OrganisationRegistrationAgency.json").json()

    publisher_codes = {publisher['code']: publisher for publisher in publishers['data']}

    org_prefixes = {prefix['code']: prefix for prefix in registration_agency['data']}

    found_publisher_orgs = {}
    found_org_prefix = {}
    not_found_orgs = {}

    regex = re.compile('^[^\/\&\|\?]+$')

    for activity in root.xpath(ACTIVITY_PREFIX):
        reporting_org = activity.xpath('reporting-org/@ref')
        iati_identifiers = activity.xpath('iati-identifier/text()')
        iati_identifier = iati_identifiers[0] if len(iati_identifiers) else None

        orgs_in_data = {
            "Participating Org": activity.xpath('participating-org/@ref'),
            "Transaction Provider": activity.xpath('transaction/provider-org/@ref'),
            "Transaction Receiver": activity.xpath('transaction/receiver-org/@ref')
        }
        org_type_template = {key: 0 for key in orgs_in_data}

        for org_type, orgs in orgs_in_data.items():
            for org in orgs:
                if org in reporting_org:
                    continue

                # get possible prefixes by initial substrings of ref. This is faster than checking ref
                # against all prefixes in registry.
                found_prefix = None
                for possible_prefix in set(org[0:n] for n in range(4, len(org)+1)):  # no prefix shorther than 4
                    if possible_prefix in org_prefixes:
                        found_prefix = possible_prefix
                        break

                if org in publisher_codes:
                    if org not in found_publisher_orgs:
                        found_publisher_orgs[org] = publisher_codes[org]
                        found_publisher_orgs[org]["count"] = 0
                        found_publisher_orgs[org]["type_count"] = org_type_template.copy()
                        found_publisher_orgs[org]["activity_ids"] = set()
                    found_publisher_orgs[org]["count"] += 1
                    found_publisher_orgs[org]["type_count"][org_type] += 1
                    if iati_identifier:
                        found_publisher_orgs[org]["activity_ids"].add(iati_identifier)

                elif found_prefix:
                    if found_prefix not in found_org_prefix:
                        found_org_prefix[found_prefix] = org_prefixes[found_prefix]
                        found_org_prefix[found_prefix]["orgs"] = set()
                        found_org_prefix[found_prefix]["count"] = 0
                        found_org_prefix[found_prefix]["type_count"] = org_type_template.copy()
                        found_org_prefix[found_prefix]["activity_ids"] = set()
                    found_org_prefix[found_prefix]["count"] += 1
                    found_org_prefix[found_prefix]["type_count"][org_type] += 1
                    found_org_prefix[found_prefix]["orgs"].add(org)
                    if iati_identifier:
                        found_org_prefix[found_prefix]["activity_ids"].add(iati_identifier)

                else:
                    if regex.match(org):
                        if org not in not_found_orgs:
                            not_found_orgs[org] = {}
                            not_found_orgs[org]["count"] = 0
                            not_found_orgs[org]["type_count"] = org_type_template.copy()
                            not_found_orgs[org]["activity_ids"] = set()
                        not_found_orgs[org]["count"] += 1
                        not_found_orgs[org]["type_count"][org_type] += 1
                        if iati_identifier:
                            not_found_orgs[org]["activity_ids"].add(iati_identifier)

    organisation_ref_stats = {"publisher_count": len(found_publisher_orgs),
                              "publisher_org_list": sorted(list(found_publisher_orgs.items()), key=lambda x: x[1]["count"], reverse=True),
                              "org_prefix_count": len(found_org_prefix),
                              "org_prefix_list": sorted(list(found_org_prefix.items()), key=lambda x: x[1]["count"], reverse=True),
                              "not_found_orgs_count": len(not_found_orgs),
                              "not_found_orgs_list": sorted(list(not_found_orgs.items()), key=lambda x: x[1]["count"], reverse=True)}

    return organisation_ref_stats
