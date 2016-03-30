from django.utils.translation import ugettext_lazy as _
from django.shortcuts import render
from cove.input.models import SuppliedData
import os
from collections import OrderedDict
import shutil
import json
import jsonref
import logging
import warnings
import flattentool
import functools
import collections
import strict_rfc3339
import datetime
from flattentool.json_input import BadlyFormedJSONError
from flattentool.schema import get_property_type_set
import requests
from jsonschema.validators import Draft4Validator as validator
from jsonschema.exceptions import ValidationError
from jsonschema import FormatChecker
from django.db.models.aggregates import Count
from django.utils import timezone
from datetime import timedelta

logger = logging.getLogger(__name__)


uniqueItemsValidator = validator.VALIDATORS.pop("uniqueItems")


def uniqueIds(validator, uI, instance, schema):
    if (
        uI and
        validator.is_type(instance, "array")
    ):
        non_unique_ids = set()
        all_ids = set()
        for item in instance:
            try:
                item_id = item.get('id')
            except AttributeError:
                # if item is not a dict
                item_id = None
            if item_id and not isinstance(item_id, list):
                if item_id in all_ids:
                    non_unique_ids.add(item_id)
                all_ids.add(item_id)
            else:
                # if there is any item without an id key, or the item is not a dict
                # revert to original validator
                for error in uniqueItemsValidator(validator, uI, instance, schema):
                    yield error
                return

        if non_unique_ids:
            yield ValidationError("Non-unique ID Values (first 3 shown):  {}".format(", ".join(list(non_unique_ids)[:3])))

validator.VALIDATORS.pop("patternProperties")
validator.VALIDATORS["uniqueItems"] = uniqueIds


def to_list(item):
    if isinstance(item, list):
        return item
    return [item]


def get_no_exception(item, key, fallback):
    try:
        return item.get(key, fallback)
    except AttributeError:
        return fallback


def update_docs(document_parent, counter):
    count = 0
    documents = document_parent.get('documents', [])
    for document in documents:
        count += 1
        doc_type = document.get("documentType")
        if doc_type:
            counter.update([doc_type])
    return count


def ignore_errors(f):
    def ignore(json_data, ignore_errors=False):
        if ignore_errors:
            try:
                return f(json_data)
            except (KeyError, TypeError, IndexError, AttributeError):
                return {}
        else:
            return f(json_data)
    return ignore


@ignore_errors
def get_releases_aggregates(json_data):
    release_count = 0
    unique_ocids = set()
    tags = collections.Counter()
    unique_lang = set()
    unique_initation_type = set()
    unique_release_ids = set()
    duplicate_release_ids = set()

    ##for matching with contracts
    unique_award_id = set()

    planning_ocids = set()
    tender_ocids = set()
    awardid_ocids = set()
    award_ocids = set()
    contractid_ocids = set()
    contract_ocids = set()
    implementation_contractid_ocids = set()
    implementation_ocids = set()

    release_dates = []
    tender_dates = []
    award_dates = []
    contract_dates = []

    unique_buyers_identifier = dict()
    unique_buyers_name_no_id = set()
    unique_suppliers_identifier = dict()
    unique_suppliers_name_no_id = set()
    unique_procuring_identifier = dict()
    unique_procuring_name_no_id = set()
    unique_tenderers_identifier = dict()
    unique_tenderers_name_no_id = set()

    unique_organisation_schemes = set()
    organisation_identifier_address = set()
    organisation_name_no_id_address = set()
    organisation_identifier_contact_point = set()
    organisation_name_no_id_contact_point = set()

    release_tender_item_ids = set()
    release_award_item_ids = set()
    release_contract_item_ids = set()
    item_identifier_schemes = set()

    unique_currency = set()

    planning_doctype = collections.Counter()
    planning_doc_count = 0
    tender_doctype = collections.Counter()
    tender_doc_count = 0
    tender_milestones_doctype = collections.Counter()
    tender_milestones_doc_count = 0
    award_doctype = collections.Counter()
    award_doc_count = 0
    contract_doctype = collections.Counter()
    contract_doc_count = 0
    implementation_doctype = collections.Counter()
    implementation_doc_count = 0
    implementation_milestones_doctype = collections.Counter()
    implementation_milestones_doc_count = 0

    def process_org(org, unique_id, unique_name):
        identifier = org.get('identifier')
        org_id = None
        if identifier:
            org_id = identifier.get('id')
            if org_id:
                unique_id[org_id] = org.get('name', '') or ''
                scheme = identifier.get('scheme')
                if scheme:
                    unique_organisation_schemes.add(scheme)
                if org.get('address'):
                    organisation_identifier_address.add(org_id)
                if org.get('contactPoint'):
                    organisation_identifier_contact_point.add(org_id)
        if not org_id:
            name = org.get('name')
            if name:
                unique_name.add(name)
            if org.get('address'):
                organisation_name_no_id_address.add(name)
            if org.get('contactPoint'):
                organisation_name_no_id_contact_point.add(name)

    def get_item_scheme(item):
        classification = item.get('classification')
        if classification:
            scheme = classification.get('scheme')
            if scheme:
                item_identifier_schemes.add(scheme)

    releases = get_no_exception(json_data, 'releases', [])
    for release in releases:
        # ### Release Section ###
        if not isinstance(release, dict):
            continue
        release_count = release_count + 1
        ocid = release.get('ocid')
        release_id = release.get('id')
        if not ocid:
            continue
        if release_id:
            if release_id in unique_release_ids:
                duplicate_release_ids.add(release_id)
            unique_release_ids.add(release_id)

        unique_ocids.add(release['ocid'])
        if 'tag' in release:
            tags.update(to_list(release['tag']))
        initiationType = release.get('initiationType')
        if initiationType:
            unique_initation_type.add(initiationType)

        releaseDate = release.get('date', '')
        if releaseDate:
            release_dates.append(str(releaseDate))

        if 'language' in release:
            unique_lang.add(release['language'])
        buyer = release.get('buyer')
        if buyer:
            process_org(buyer, unique_buyers_identifier, unique_buyers_name_no_id)

        # ### Planning Section ###
        planning = get_no_exception(release, 'planning', {})
        if planning and isinstance(planning, dict):
            planning_ocids.add(ocid)
            planning_doc_count += update_docs(planning, planning_doctype)

        # ### Tender Section ###
        tender = get_no_exception(release, 'tender', {})
        if tender and isinstance(tender, dict):
            tender_ocids.add(ocid)
            tender_doc_count += update_docs(tender, tender_doctype)
            tender_period = tender.get('tenderPeriod')
            if tender_period:
                start_date = tender_period.get('startDate', '')
                if start_date:
                    tender_dates.append(str(start_date))
            procuringEntity = tender.get('procuringEntity')
            if procuringEntity:
                process_org(procuringEntity, unique_procuring_identifier, unique_procuring_name_no_id)
            tenderers = tender.get('tenderers', [])
            for tenderer in tenderers:
                process_org(tenderer, unique_tenderers_identifier, unique_tenderers_name_no_id)
            tender_items = tender.get('items', [])
            for item in tender_items:
                item_id = item.get('id')
                if item_id and release_id:
                    release_tender_item_ids.add((ocid, release_id, item_id))
                get_item_scheme(item)
            milestones = tender.get('milestones')
            if milestones:
                for milestone in milestones:
                    tender_milestones_doc_count += update_docs(milestone, tender_milestones_doctype)

        # ### Award Section ###
        awards = get_no_exception(release, 'awards', [])
        for award in awards:
            if not isinstance(award, dict):
                continue
            award_id = award.get('id')
            award_ocids.add(ocid)
            if award_id:
                unique_award_id.add(award_id)
                awardid_ocids.add((award_id, ocid))
            award_date = award.get('date', '')
            if award_date:
                award_dates.append(str(award_date))
            award_items = award.get('items', [])
            for item in award_items:
                item_id = item.get('id')
                if item_id and release_id and award_id:
                    release_award_item_ids.add((ocid, release_id, award_id, item_id))
                get_item_scheme(item)
            suppliers = award.get('suppliers', [])
            for supplier in suppliers:
                process_org(supplier, unique_suppliers_identifier, unique_suppliers_name_no_id)
            award_doc_count += update_docs(award, award_doctype)

        # ### Contract section
        contracts = get_no_exception(release, 'contracts', [])
        for contract in contracts:
            if not isinstance(contract, dict):
                continue
            contract_id = contract.get('id')
            contract_ocids.add(ocid)
            if contract_id:
                contractid_ocids.add((contract_id, ocid))
            period = contract.get('period')
            if period:
                start_date = period.get('startDate', '')
                if start_date:
                    contract_dates.append(start_date)
            contract_items = contract.get('items', [])
            for item in contract_items:
                item_id = item.get('id')
                if item_id and release_id and contract_id:
                    release_contract_item_ids.add((ocid, release_id, contract_id, item_id))
                get_item_scheme(item)
            contract_doc_count += update_docs(contract, contract_doctype)
            implementation = contract.get('implementation')
            if implementation:
                implementation_ocids.add(ocid)
                if contract_id:
                    implementation_contractid_ocids.add((contract_id, ocid))
                implementation_doc_count += update_docs(implementation, implementation_doctype)
                implementation_milestones = implementation.get('milestones', [])
                for milestone in implementation_milestones:
                    implementation_milestones_doc_count += update_docs(milestone, implementation_milestones_doctype)

    contracts_without_awards = []
    for release in releases:
        contracts = release.get('contracts', [])
        for contract in contracts:
            awardID = contract.get('awardID')
            if awardID not in unique_award_id:
                contracts_without_awards.append(contract)

    unique_buyers_count = len(unique_buyers_identifier) + len(unique_buyers_name_no_id)
    unique_buyers = [name + ' (' + str(id) + ')' for id, name in unique_buyers_identifier.items()] + list(unique_buyers_name_no_id)

    unique_suppliers_count = len(unique_suppliers_identifier) + len(unique_suppliers_name_no_id)
    unique_suppliers = [name + ' (' + str(id) + ')' for id, name in unique_suppliers_identifier.items()] + list(unique_suppliers_name_no_id)

    unique_procuring_count = len(unique_procuring_identifier) + len(unique_procuring_name_no_id)
    unique_procuring = [name + ' (' + str(id) + ')' for id, name in unique_procuring_identifier.items()] + list(unique_procuring_name_no_id)

    unique_tenderers_count = len(unique_tenderers_identifier) + len(unique_tenderers_name_no_id)
    unique_tenderers = [name + ' (' + str(id) + ')' for id, name in unique_tenderers_identifier.items()] + list(unique_tenderers_name_no_id)

    unique_org_identifier_count = len(set(unique_buyers_identifier) |
                                      set(unique_suppliers_identifier) |
                                      set(unique_procuring_identifier) |
                                      set(unique_tenderers_identifier))
    unique_org_name_count = len(unique_buyers_name_no_id |
                                unique_suppliers_name_no_id |
                                unique_procuring_name_no_id |
                                unique_tenderers_name_no_id)
    unique_org_count = unique_org_identifier_count + unique_org_name_count

    def get_currencies(object):
        if isinstance(object, dict):
            for key, value in object.items():
                if key == 'currency':
                    unique_currency.add(value)
                get_currencies(value)
        if isinstance(object, list):
            for item in object:
                get_currencies(item)
    get_currencies(json_data)

    return dict(
        release_count=release_count,
        unique_ocids=unique_ocids,
        unique_initation_type=unique_initation_type,
        duplicate_release_ids=duplicate_release_ids,
        tags=dict(tags),
        unique_lang=unique_lang,
        unique_award_id=unique_award_id,

        planning_count=len(planning_ocids),
        tender_count=len(tender_ocids),
        award_count=len(awardid_ocids),
        processes_award_count=len(award_ocids),
        contract_count=len(contractid_ocids),
        processes_contract_count=len(contract_ocids),
        implementation_count=len(implementation_contractid_ocids),
        processes_implementation_count=len(implementation_ocids),

        min_release_date=min(release_dates) if release_dates else '',
        max_release_date=max(release_dates) if release_dates else '',
        min_tender_date=min(tender_dates) if tender_dates else '',
        max_tender_date=max(tender_dates) if tender_dates else '',
        min_award_date=min(award_dates) if award_dates else '',
        max_award_date=max(award_dates) if award_dates else '',
        min_contract_date=min(contract_dates) if contract_dates else '',
        max_contract_date=max(contract_dates) if contract_dates else '',

        unique_buyers_identifier=unique_buyers_identifier,
        unique_buyers_name_no_id=unique_buyers_name_no_id,
        unique_suppliers_identifier=unique_suppliers_identifier,
        unique_suppliers_name_no_id=unique_suppliers_name_no_id,
        unique_procuring_identifier=unique_procuring_identifier,
        unique_procuring_name_no_id=unique_procuring_name_no_id,
        unique_tenderers_identifier=unique_tenderers_identifier,
        unique_tenderers_name_no_id=unique_tenderers_name_no_id,

        unique_buyers=set(unique_buyers),
        unique_suppliers=set(unique_suppliers),
        unique_procuring=set(unique_procuring),
        unique_tenderers=set(unique_tenderers),

        unique_buyers_count=unique_buyers_count,
        unique_suppliers_count=unique_suppliers_count,
        unique_procuring_count=unique_procuring_count,
        unique_tenderers_count=unique_tenderers_count,

        unique_org_identifier_count=unique_org_identifier_count,
        unique_org_name_count=unique_org_name_count,
        unique_org_count=unique_org_count,

        unique_organisation_schemes=unique_organisation_schemes,

        organisations_with_address=len(organisation_identifier_address) + len(organisation_name_no_id_address),
        organisations_with_contact_point=len(organisation_identifier_contact_point) + len(organisation_name_no_id_contact_point),

        total_item_count=len(release_tender_item_ids) + len(release_award_item_ids) + len(release_contract_item_ids),
        tender_item_count=len(release_tender_item_ids),
        award_item_count=len(release_award_item_ids),
        contract_item_count=len(release_contract_item_ids),

        item_identifier_schemes=item_identifier_schemes,
        unique_currency=unique_currency,

        planning_doc_count=planning_doc_count,
        tender_doc_count=tender_doc_count,
        tender_milestones_doc_count=tender_milestones_doc_count,
        award_doc_count=award_doc_count,
        contract_doc_count=contract_doc_count,
        implementation_doc_count=implementation_doc_count,
        implementation_milestones_doc_count=implementation_milestones_doc_count,

        planning_doctype=dict(planning_doctype),
        tender_doctype=dict(tender_doctype),
        tender_milestones_doctype=dict(tender_milestones_doctype),
        award_doctype=dict(award_doctype),
        contract_doctype=dict(contract_doctype),
        implementation_doctype=dict(implementation_doctype),
        implementation_milestones_doctype=dict(implementation_milestones_doctype),

        contracts_without_awards=contracts_without_awards,
    )


@ignore_errors
def get_records_aggregates(json_data):
    # Unique ocids
    unique_ocids = set()

    if 'records' in json_data:
        for record in json_data['records']:
            # Gather all the ocids
            if 'ocid' in record:
                unique_ocids.add(record['ocid'])

    # Number of records
    count = len(json_data['records']) if 'records' in json_data else 0

    return {
        'count': count,
        'unique_ocids': unique_ocids,
    }


@ignore_errors
def get_grants_aggregates(json_data):

    id_count = 0
    count = 0
    unique_ids = set()
    duplicate_ids = set()
    max_award_date = ""
    min_award_date = ""
    max_amount_awarded = 0
    min_amount_awarded = 0
    distinct_funding_org_identifier = set()
    distinct_recipient_org_identifier = set()
    distinct_currency = set()

    if 'grants' in json_data:
        for grant in json_data['grants']:
            count = count + 1
            amountAwarded = grant.get('amountAwarded')
            if amountAwarded and isinstance(amountAwarded, (int, float)):
                max_amount_awarded = max(amountAwarded, max_amount_awarded)
                if not min_amount_awarded:
                    min_amount_awarded = amountAwarded
                min_amount_awarded = min(amountAwarded, min_amount_awarded)
            awardDate = str(grant.get('awardDate', ''))
            if awardDate:
                max_award_date = max(awardDate, max_award_date)
                if not min_award_date:
                    min_award_date = awardDate
                min_award_date = min(awardDate, min_award_date)
            grant_id = grant.get('id')
            if grant_id:
                id_count = id_count + 1
                if grant_id in unique_ids:
                    duplicate_ids.add(grant_id)
                unique_ids.add(grant_id)
            funding_orgs = grant.get('fundingOrganization', [])
            for funding_org in funding_orgs:
                funding_org_id = funding_org.get('id')
                if funding_org_id:
                    distinct_funding_org_identifier.add(funding_org_id)
            recipient_orgs = grant.get('recipientOrganization', [])
            for recipient_org in recipient_orgs:
                recipient_org_id = recipient_org.get('id')
                if recipient_org_id:
                    distinct_recipient_org_identifier.add(recipient_org_id)
            currency = grant.get('currency')
            if currency:
                distinct_currency.add(currency)

    return {
        'count': count,
        'id_count': id_count,
        'unique_ids': unique_ids,
        'duplicate_ids': duplicate_ids,
        'max_award_date': max_award_date,
        'min_award_date': min_award_date,
        'max_amount_awarded': max_amount_awarded,
        'min_amount_awarded': min_amount_awarded,
        'distinct_funding_org_identifier': distinct_funding_org_identifier,
        'distinct_recipient_org_identifier': distinct_recipient_org_identifier,
        'distinct_currency': distinct_currency
    }


def fields_present_generator(json_data, prefix=''):
    if not isinstance(json_data, dict):
        return
    for key, value in json_data.items():
        if isinstance(value, list):
            for item in value:
                if isinstance(item, dict):
                    yield from fields_present_generator(item, prefix + '/' + key)
            yield prefix + '/' + key
        elif isinstance(value, dict):
            yield from fields_present_generator(value, prefix + '/' + key)
            yield prefix + '/' + key
        else:
            # if a string value has an underscore in it, assume its a language property
            # and do not count as a present field.
            if '_' not in key:
                yield prefix + '/' + key


def get_fields_present(*args, **kwargs):
    counter = collections.Counter()
    counter.update(fields_present_generator(*args, **kwargs))
    return dict(counter)


def schema_dict_fields_generator(schema_dict):
    if 'properties' in schema_dict:
        for property_name, value in schema_dict['properties'].items():
            if 'oneOf' in value:
                property_schema_dicts = value['oneOf']
            else:
                property_schema_dicts = [value]
            for property_schema_dict in property_schema_dicts:
                property_type_set = get_property_type_set(property_schema_dict)
                if 'object' in property_type_set:
                    for field in schema_dict_fields_generator(property_schema_dict):
                        yield '/' + property_name + field
                elif 'array' in property_type_set:
                    fields = schema_dict_fields_generator(property_schema_dict['items'])
                    for field in fields:
                        yield '/' + property_name + field
                yield '/' + property_name


def get_schema_fields(schema_filename):
    r = requests.get(schema_filename)
    return set(schema_dict_fields_generator(jsonref.loads(r.text, object_pairs_hook=OrderedDict)))


def get_counts_additional_fields(schema_url, json_data):
    fields_present = get_fields_present(json_data)
    schema_fields = get_schema_fields(schema_url)
    data_only_all = set(fields_present) - schema_fields
    data_only = set()
    for field in data_only_all:
        parent_field = "/".join(field.split('/')[:-1])
        # only take fields with parent in schema (and top level fields)
        # to make results less verbose
        if not parent_field or parent_field in schema_fields:
            data_only.add(field)

    return [('/'.join(key.split('/')[:-1]), key.split('/')[-1], fields_present[key]) for key in data_only]


def datetime_or_date(instance):
    result = strict_rfc3339.validate_rfc3339(instance)
    if result:
        return result
    return datetime.datetime.strptime(instance, "%Y-%m-%d")


def get_schema_validation_errors(json_data, schema_url, current_app):
    schema = requests.get(schema_url).json()
    validation_errors = collections.defaultdict(list)
    format_checker = FormatChecker()
    if current_app == 'cove-360':
        format_checker.checkers['date-time'] = (datetime_or_date, ValueError)
    for n, e in enumerate(validator(schema, format_checker=format_checker).iter_errors(json_data)):
        validation_errors[e.message].append("/".join(str(item) for item in e.path))
    return dict(validation_errors)
    

class CoveInputDataError(Exception):
    """
    An error that we think is due to the data input by the user, rather than a
    bug in the application.
    """
    def __init__(self, context=None):
        if context:
            self.context = context

    @staticmethod
    def error_page(func):
        @functools.wraps(func)
        def wrapper(request, *args, **kwargs):
            try:
                return func(request, *args, **kwargs)
            except CoveInputDataError as err:
                return render(request, 'error.html', context=err.context)
        return wrapper


class UnrecognisedFileType(CoveInputDataError):
    context = {
        'sub_title': _("Sorry we can't process that data"),
        'link': 'cove:index',
        'link_text': _('Try Again'),
        'msg': _('We did not recognise the file type.\n\nWe can only process json, csv and xlsx files.')
    }


def get_file_type(django_file):
    if django_file.name.endswith('.json'):
        return 'json'
    elif django_file.name.endswith('.xlsx'):
        return 'xlsx'
    elif django_file.name.endswith('.csv'):
        return 'csv'
    else:
        first_byte = django_file.read(1)
        if first_byte in [b'{', b'[']:
            return 'json'
        else:
            raise UnrecognisedFileType


def convert_json(request, data):
    context = {}
    converted_path = os.path.join(data.upload_dir(), 'flattened')
    flatten_kwargs = dict(
        output_name=converted_path,
        main_sheet_name=request.cove_config['main_sheet_name'],
        root_list_path=request.cove_config['main_sheet_name'],
        root_id=request.cove_config['root_id'],
        schema=request.cove_config['item_schema_url'],
    )
    try:
        conversion_warning_cache_path = os.path.join(data.upload_dir(), 'conversion_warning_messages.json')
        if not os.path.exists(converted_path + '.xlsx'):
            with warnings.catch_warnings(record=True) as conversion_warnings:
                if request.POST.get('flatten'):
                    flattentool.flatten(data.original_file.file.name, **flatten_kwargs)
                else:
                    return {'conversion': 'flattenable'}
                context['converted_file_size'] = os.path.getsize(converted_path + '.xlsx')
                context['conversion_warning_messages'] = [str(w.message) for w in conversion_warnings]
            with open(conversion_warning_cache_path, 'w+') as fp:
                json.dump(context['conversion_warning_messages'], fp)
        elif os.path.exists(conversion_warning_cache_path):
            with open(conversion_warning_cache_path) as fp:
                context['conversion_warning_messages'] = json.load(fp)

        conversion_warning_cache_path_titles = os.path.join(data.upload_dir(), 'conversion_warning_messages_titles.json')

        if request.cove_config['convert_titles']:
            with warnings.catch_warnings(record=True) as conversion_warnings_titles:
                flatten_kwargs.update(dict(
                    output_name=converted_path + '-titles',
                    use_titles=True
                ))
                if not os.path.exists(converted_path + '-titles.xlsx'):
                    flattentool.flatten(data.original_file.file.name, **flatten_kwargs)
                context['converted_file_size_titles'] = os.path.getsize(converted_path + '-titles.xlsx')
                context['conversion_warning_messages_titles'] = [str(w.message) for w in conversion_warnings_titles]
            with open(conversion_warning_cache_path_titles, 'w+') as fp:
                json.dump(context['conversion_warning_messages_titles'], fp)
        elif os.path.exists(conversion_warning_cache_path_titles):
            with open(conversion_warning_cache_path_titles) as fp:
                context['conversion_warning_messages_titles'] = json.load(fp)

    except BadlyFormedJSONError as err:
        raise CoveInputDataError(context={
            'sub_title': _("Sorry we can't process that data"),
            'link': 'cove:index',
            'link_text': _('Try Again'),
            'msg': _('We think you tried to upload a JSON file, but it is not well formed JSON.\n\nError message: {}'.format(err))
        })
    except Exception as err:
        logger.exception(err, extra={
            'request': request,
            })
        return {
            'conversion': 'flatten',
            'conversion_error': repr(err)
        }
    context.update({
        'conversion': 'flatten',
        'converted_path': converted_path,
        'converted_url': '{}/flattened'.format(data.upload_url())
    })
    return context


def convert_spreadsheet(request, data, file_type):
    context = {}
    converted_path = os.path.join(data.upload_dir(), 'unflattened.json')
    encoding = 'utf-8'
    if file_type == 'csv':
        # flatten-tool expects a directory full of CSVs with file names
        # matching what xlsx titles would be.
        # If only one upload file is specified, we rename it and move into
        # a new directory, such that it fits this pattern.
        input_name = os.path.join(data.upload_dir(), 'csv_dir')
        os.makedirs(input_name, exist_ok=True)
        destination = os.path.join(input_name, request.cove_config['main_sheet_name'] + '.csv')
        shutil.copy(data.original_file.file.name, destination)
        try:
            with open(destination, encoding='utf-8') as main_sheet_file:
                main_sheet_file.read()
        except UnicodeDecodeError:
            try:
                with open(destination, encoding='cp1252') as main_sheet_file:
                    main_sheet_file.read()
                encoding = 'cp1252'
            except UnicodeDecodeError:
                encoding = 'latin_1'
    else:
        input_name = data.original_file.file.name
    try:
        conversion_warning_cache_path = os.path.join(data.upload_dir(), 'conversion_warning_messages.json')
        if not os.path.exists(converted_path):
            with warnings.catch_warnings(record=True) as conversion_warnings:
                flattentool.unflatten(
                    input_name,
                    output_name=converted_path,
                    input_format=file_type,
                    main_sheet_name=request.cove_config['main_sheet_name'],
                    root_id=request.cove_config['root_id'],
                    schema=request.cove_config['item_schema_url'],
                    convert_titles=True,
                    encoding=encoding
                )
                context['conversion_warning_messages'] = [str(w.message) for w in conversion_warnings]
            with open(conversion_warning_cache_path, 'w+') as fp:
                json.dump(context['conversion_warning_messages'], fp)
        elif os.path.exists(conversion_warning_cache_path):
            with open(conversion_warning_cache_path) as fp:
                context['conversion_warning_messages'] = json.load(fp)

        context['converted_file_size'] = os.path.getsize(converted_path)
    except Exception as err:
        logger.exception(err, extra={
            'request': request,
            })
        raise CoveInputDataError({
            'sub_title': _("Sorry we can't process that data"),
            'link': 'cove:index',
            'link_text': _('Try Again'),
            'msg': _('We think you tried to supply a spreadsheet, but we failed to convert it to JSON.\n\nError message: {}'.format(repr(err)))
        })

    context.update({
        'conversion': 'unflatten',
        'converted_path': converted_path,
        'converted_url': '{}/unflattened.json'.format(data.upload_url())
    })
    return context


@CoveInputDataError.error_page
def explore(request, pk):
    if request.current_app == 'cove-resourceprojects':
        import cove.dataload.views
        return cove.dataload.views.data(request, pk)

    try:
        data = SuppliedData.objects.get(pk=pk)
    except (SuppliedData.DoesNotExist, ValueError):  # Catches: Primary key does not exist, and, badly formed hexadecimal UUID string
        return render(request, 'error.html', {
            'sub_title': _('Sorry, the page you are looking for is not available'),
            'link': 'cove:index',
            'link_text': _('Go to Home page'),
            'msg': _("We don't seem to be able to find the data you requested.")
            }, status=404)
    
    try:
        data.original_file.file.name
    except FileNotFoundError:
        return render(request, 'error.html', {
            'sub_title': _('Sorry, the page you are looking for is not available'),
            'link': 'cove:index',
            'link_text': _('Go to Home page'),
            'msg': _('The data you were hoping to explore no longer exists.\n\nThis is because all data suplied to this website is automatically deleted after 7 days, and therefore the analysis of that data is no longer available.')
        }, status=404)
    
    file_type = get_file_type(data.original_file)

    context = {
        "original_file": {
            "url": data.original_file.url,
            "size": data.original_file.size
        },
        "current_url": request.build_absolute_uri(),
        "source_url": data.source_url,
        "created_date": data.created,
    }

    if file_type == 'json':
        # open the data first so we can inspect for record package
        with open(data.original_file.file.name, encoding='utf-8') as fp:
            try:
                json_data = json.load(fp)
            except ValueError as err:
                raise CoveInputDataError(context={
                    'sub_title': _("Sorry we can't process that data"),
                    'link': 'cove:index',
                    'link_text': _('Try Again'),
                    'msg': _('We think you tried to upload a JSON file, but it is not well formed JSON.\n\nError message: {}'.format(err))
                })
        if request.current_app == 'cove-ocds' and 'records' in json_data:
            context['conversion'] = None
        else:
            context.update(convert_json(request, data))
    else:
        context.update(convert_spreadsheet(request, data, file_type))
        with open(context['converted_path'], encoding='utf-8') as fp:
            json_data = json.load(fp)

    schema_url = request.cove_config['schema_url']

    if request.current_app == 'cove-ocds':
        schema_url = schema_url['record'] if 'records' in json_data else schema_url['release']

    if schema_url:
        context.update({
            'data_only': sorted(get_counts_additional_fields(schema_url, json_data))
        })

    validation_errors_path = os.path.join(data.upload_dir(), 'validation_errors.json')
    if os.path.exists(validation_errors_path):
        with open(validation_errors_path) as validiation_error_fp:
            validation_errors = json.load(validiation_error_fp)
    else:
        validation_errors = get_schema_validation_errors(json_data, schema_url, request.current_app) if schema_url else None
        with open(validation_errors_path, 'w+') as validiation_error_fp:
            validiation_error_fp.write(json.dumps(validation_errors))

    context.update({
        'file_type': file_type,
        'schema_url': schema_url,
        'validation_errors': validation_errors,
        'json_data': json_data  # Pass the JSON data to the template so we can display values that need little processing
    })

    view = 'explore.html'
    if request.current_app == 'cove-ocds':
        if 'records' in json_data:
            context['records_aggregates'] = get_records_aggregates(json_data)
            view = 'explore_ocds-record.html'
        else:
            context['releases_aggregates'] = get_releases_aggregates(json_data, ignore_errors=bool(validation_errors))
            view = 'explore_ocds-release.html'
    elif request.current_app == 'cove-360':
        context['grants_aggregates'] = get_grants_aggregates(json_data)
        view = 'explore_360.html'

    return render(request, view, context)


def stats(request):
    query = SuppliedData.objects.filter(current_app=request.current_app)
    by_form = query.values('form_name').annotate(Count('id'))
    return render(request, 'stats.html', {
        'uploaded': query.count(),
        'total_by_form': {x['form_name']: x['id__count'] for x in by_form},
        'upload_by_time_by_form': [(
            num_days,
            query.filter(created__gt=timezone.now() - timedelta(days=num_days)).count(),
            {x['form_name']: x['id__count'] for x in by_form.filter(created__gt=timezone.now() - timedelta(days=num_days))}
        ) for num_days in [1, 7, 30]],
    })
