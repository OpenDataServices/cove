import json
import re
import os
from collections import defaultdict, OrderedDict

import requests

import cove.lib.tools as tools


# JSON from link on http://iatistandard.org/202/codelists/OrganisationRegistrationAgency/
try:
    org_prefix_codelist = requests.get('http://iatistandard.org/202/codelists/downloads/clv3/json/en/OrganisationRegistrationAgency.json').json()
except requests.exceptions.RequestException:
    local_codelist_file = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'OrganisationRegistrationAgency.json')
    with open(local_codelist_file) as local_codelist:
        org_prefix_codelist = json.load(local_codelist)

org_prefixes = [x['code'] for x in org_prefix_codelist['data']]
org_prefixes.append('360G')

currency_html = {
    "GBP": "&pound;",
    "USD": "$",
    "EUR": "&euro;"
}


@tools.ignore_errors
def get_grants_aggregates(json_data):

    id_count = 0
    count = 0
    unique_ids = set()
    duplicate_ids = set()
    max_award_date = ""
    min_award_date = ""
    distinct_funding_org_identifier = set()
    distinct_recipient_org_identifier = set()
    currencies = {}

    if 'grants' in json_data:
        for grant in json_data['grants']:
            count = count + 1
            currency = grant.get('currency')

            if currency not in currencies.keys():
                currencies[currency] = {
                    "count": 0,
                    "total_amount": 0,
                    "max_amount": 0,
                    "min_amount": 0,
                    "currency_symbol": currency_html.get(currency, "")
                }

            currencies[currency]["count"] += 1
            amount_awarded = grant.get('amountAwarded')
            if amount_awarded and isinstance(amount_awarded, (int, float)):
                currencies[currency]["total_amount"] += amount_awarded
                currencies[currency]['max_amount'] = max(amount_awarded, currencies[currency]['max_amount'])
                if not currencies[currency]["min_amount"]:
                    currencies[currency]['min_amount'] = amount_awarded
                currencies[currency]['min_amount'] = min(amount_awarded, currencies[currency]['min_amount'])

            award_date = str(grant.get('awardDate', ''))
            if award_date:
                max_award_date = max(award_date, max_award_date)
                if not min_award_date:
                    min_award_date = award_date
                min_award_date = min(award_date, min_award_date)

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

    recipient_org_prefixes = get_prefixes(distinct_recipient_org_identifier)
    recipient_org_identifier_prefixes = recipient_org_prefixes['prefixes']
    recipient_org_identifiers_unrecognised_prefixes = recipient_org_prefixes['unrecognised_prefixes']
    
    funding_org_prefixes = get_prefixes(distinct_funding_org_identifier)
    funding_org_identifier_prefixes = funding_org_prefixes['prefixes']
    funding_org_identifiers_unrecognised_prefixes = funding_org_prefixes['unrecognised_prefixes']

    return {
        'count': count,
        'id_count': id_count,
        'unique_ids': unique_ids,
        'duplicate_ids': duplicate_ids,
        'max_award_date': max_award_date.split("T")[0],
        'min_award_date': min_award_date.split("T")[0],
        'distinct_funding_org_identifier': distinct_funding_org_identifier,
        'distinct_recipient_org_identifier': distinct_recipient_org_identifier,
        'currencies': currencies,
        'recipient_org_identifier_prefixes': recipient_org_identifier_prefixes,
        'recipient_org_identifiers_unrecognised_prefixes': recipient_org_identifiers_unrecognised_prefixes,
        'funding_org_identifier_prefixes': funding_org_identifier_prefixes,
        'funding_org_identifiers_unrecognised_prefixes': funding_org_identifiers_unrecognised_prefixes
    }


def get_prefixes(distinct_identifiers):

    org_identifier_prefixes = defaultdict(int)
    org_identifiers_unrecognised_prefixes = defaultdict(int)

    for org_identifier in distinct_identifiers:
        for prefix in org_prefixes:
            if org_identifier.startswith(prefix):
                org_identifier_prefixes[prefix] += 1
                break
        else:
            org_identifiers_unrecognised_prefixes[org_identifier] += 1
    
    return {
        'prefixes': org_identifier_prefixes,
        'unrecognised_prefixes': org_identifiers_unrecognised_prefixes,
    }


def check_charity_number(charity_number):
    charity_number = str(charity_number)
    is_int = True
    try:
        int(charity_number)
    except ValueError:
        is_int = False

    if len(charity_number) in (6, 7) and is_int:
        return True

    return False


def check_company_number(company_number):
    if len(str(company_number)) != 8:
        return False
    try:
        int(str(company_number)[2:])
    except ValueError:
        return False

    return True


def flatten_dict(grant, path=""):
    for key, value in sorted(grant.items()):
        if isinstance(value, list):
            for num, item in enumerate(value):
                if isinstance(item, dict):
                    yield from flatten_dict(item, "{}/{}/{}".format(path, key, num))
                else:
                    yield ("{}/{}/{}".format(path, key, num), item)
        elif isinstance(value, dict):
            yield from flatten_dict(value, "{}/{}".format(path, key))
        else:
            yield ("{}/{}".format(path, key), value)


class AdditionalTest():
    def __init__(self, **kw):
        self.grants = kw['grants']
        self.json_locations = []
        self.failed = False
        self.count = 0
        self.heading = None
        self.message = None

    def process(self, grant, path_prefix):
        pass

    def produce_message(self):
        return {
            'heading': self.heading,
            'message': self.message
        }

    def format_heading_count(self, message, verb='have'):
        '''Build a string with count of grants plus message
        
        The grant count phrase for the test is pluralized and
        prepended to message, eg: 1 grant has + message,
        2 grants have + message or 3 grants contain + message.
        '''
        noun = 'grant' if self.count == 1 else 'grants'
        if verb == 'have':
            verb = 'has' if self.count == 1 else verb
        elif verb == 'do':
            verb = 'does' if self.count == 1 else verb
        else:
            # Naively!
            verb = verb + 's' if self.count == 1 else verb
        return '{} {} {} {}'.format(self.count, noun, verb, message)


class ZeroAmountTest(AdditionalTest):
    def process(self, grant, path_prefix):
        try:
            # check for == 0 explicitly, as other falsey values will be caught
            # by schema validation, and also showing a message about 0 value
            # grants would be more confusing
            if grant['amountAwarded'] == 0:
                self.failed = True
                self.json_locations.append(path_prefix + '/amountAwarded')
                self.count += 1
        except KeyError:
            pass

        self.heading = self.format_heading_count('a value of £0')
        self.message = "It’s worth taking a look at these grants and deciding if they should be published. It’s unusual to have grants of £0, but there may be a reasonable explanation. Additional information on why these grants are £0 might be useful to anyone using the data, so consider adding an explanation to the description of the grant."


class RecipientOrg360GPrefix(AdditionalTest):
    def process(self, grant, path_prefix):
        try:
            for num, organization in enumerate(grant['recipientOrganization']):
                if organization['id'].lower().startswith('360g'):
                    self.failed = True
                    self.json_locations.append(path_prefix + '/recipientOrganization/{}/id'.format(num))
                    self.count += 1
        except KeyError:
            pass

        self.heading = self.format_heading_count("a Recipient Org:Identifier that starts '360G-'")
        self.message = "If the grant is from a recipient organisation that has an external identifier (such as a charity number, company number, or in the case of local authorities, geocodes), then this should be used instead. If no other identifier can be used, then this notice can be ignored."


class FundingOrg360GPrefix(AdditionalTest):
    def process(self, grant, path_prefix):
        try:
            for num, organization in enumerate(grant['fundingOrganization']):
                if organization['id'].lower().startswith('360g'):
                    self.failed = True
                    self.json_locations.append(path_prefix + '/fundingOrganization/{}/id'.format(num))
                    self.count += 1
        except KeyError:
            pass

        self.heading = self.format_heading_count("a Funding Org:Identifier that starts '360G-'")
        self.message = "If the grant is from a recipient organisation that has an external identifier (such as a charity number, company number, or in the case of local authorities, geocodes), then this should be used instead. If no other identifier can be used, then this notice can be ignored."


class RecipientOrgUnrecognisedPrefix(AdditionalTest):
    def process(self, grant, path_prefix):
        try:
            count_failure = False
            for num, organization in enumerate(grant['recipientOrganization']):
                for prefix in org_prefixes:
                    if organization['id'].lower().startswith(prefix.lower()):
                        break
                else:
                    self.failed = True
                    count_failure = True
                    self.json_locations.append(path_prefix + '/recipientOrganization/{}/id'.format(num))

            if count_failure:
                self.count += 1
        except KeyError:
            pass

        self.heading = "{}% of your grants have a Recipient Org:Identifier that doesn’t draw from an external identification body".format(int(round(self.count / len(self.grants) * 100)))
        self.message = "Using external identifiers (e.g. a charity number or a company number) helps people using your data to match it up against other data - for example to see who else has given grants to the same recipient, even if they’re known by a different name. If the data describes lots of grants to organisations that don’t have such identifiers or individuals then you can ignore this notice."


class FundingOrgUnrecognisedPrefix(AdditionalTest):
    def process(self, grant, path_prefix):
        try:
            count_failure = False
            for num, organization in enumerate(grant['fundingOrganization']):
                for prefix in org_prefixes:
                    if organization['id'].lower().startswith(prefix.lower()):
                        break
                else:
                    self.failed = True
                    count_failure = True
                    self.json_locations.append(path_prefix + '/fundingOrganization/{}/id'.format(num))

            if count_failure:
                self.count += 1
        except KeyError:
            pass

        self.heading = "{}% of your grants have a Funding Org:Identifier that doesn’t draw from an external identification body".format(int(round(self.count / len(self.grants) * 100)))
        self.message = "Using external identifiers (e.g. a charity number or a company number) helps people using your data to match it up against other data - for example to see who else has given grants to the same recipient, even if they’re known by a different name. If the data describes lots of grants to organisations that don’t have such identifiers or individuals then you can ignore this notice."


class RecipientOrgCharityNumber(AdditionalTest):
    def process(self, grant, path_prefix):
        try:
            count_failure = False
            for num, organization in enumerate(grant['recipientOrganization']):
                charity_number = organization['charityNumber']
                charity_number = str(charity_number)
                if charity_number[:2].isalpha():
                    charity_number = charity_number[2:]
                if not check_charity_number(charity_number):
                    self.failed = True
                    count_failure = True
                    self.json_locations.append(path_prefix + '/recipientOrganization/{}/charityNumber'.format(num))

            if count_failure:
                self.count += 1
        except KeyError:
            pass

        self.heading = self.format_heading_count("a value provided in the Recipient Org: Charity Number column that doesn’t look like a charity number")
        self.message = "Common causes of this are missing leading digits, typos or incorrect values being entered into this field."


class RecipientOrgCompanyNumber(AdditionalTest):
    def process(self, grant, path_prefix):
        try:
            count_failure = False
            for num, organization in enumerate(grant['recipientOrganization']):
                company_number = organization['companyNumber']
                if not check_company_number(company_number):
                    self.failed = True
                    count_failure = True
                    self.json_locations.append(path_prefix + '/recipientOrganization/{}/companyNumber'.format(num))

            if count_failure:
                self.count += 1
        except KeyError:
            pass

        self.heading = self.format_heading_count("a value provided in the Recipient Org: Company Number column that doesn’t look like a company number")
        self.message = "Common causes of this are missing leading digits, typos or incorrect values being entered into this field."


class MoreThanOneFundingOrg(AdditionalTest):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.funding_organization_ids = []

    def process(self, grant, path_prefix):
        try:
            for num, organization in enumerate(grant['fundingOrganization']):
                if organization.get('id') and organization.get('id') not in self.funding_organization_ids:
                    self.funding_organization_ids.append(organization['id'])
                    self.json_locations.append(path_prefix + '/fundingOrganization/{}/id'.format(num))
        except KeyError:
            pass
        if len(self.funding_organization_ids) > 1:
            self.failed = True

        self.heading = "There are {} different funding organisation IDs listed".format(len(self.funding_organization_ids))
        self.message = "If you are expecting to be publishing data for multiple funders then this notice can be ignored, however if you are only publishing for a single funder then you should review your Funder ID column to see where multiple IDs have occurred."


compiled_email_re = re.compile('[\w.-]+@[\w.-]+\.[\w.-]+')


class LooksLikeEmail(AdditionalTest):
    def process(self, grant, path_prefix):
        flattened_grant = OrderedDict(flatten_dict(grant))
        for key, value in flattened_grant.items():
            if isinstance(value, str) and compiled_email_re.search(value):
                self.failed = True
                self.json_locations.append(path_prefix + key)
                self.count += 1

        self.heading = self.format_heading_count("text that looks like an email address", verb='contain')
        self.message = "This may indicate that the data contains personal data, use and distribution of which is restricted by the Data Protection Act. You should ensure that any personal data is included with the knowledge and consent of the person to whom it refers."


class NoGrantProgramme(AdditionalTest):
    def process(self, grant, path_prefix):
        grant_programme = grant.get("grantProgramme")
        if not grant_programme:
            self.failed = True
            self.count += 1
            self.json_locations.append(path_prefix + '/id')

        self.heading = self.format_heading_count("not contain any Grant Programme fields", verb='do')
        self.message = "Although not required by the 360Giving Standard, providing Grant Programme data if available helps users to better understand your data."


class NoBeneficiaryLocation(AdditionalTest):
    def process(self, grant, path_prefix):
        beneficiary_location = grant.get("beneficiaryLocation")
        if not beneficiary_location:
            self.failed = True
            self.count += 1
            self.json_locations.append(path_prefix + '/id')

        self.heading = self.format_heading_count("not contain any beneficiary location fields", verb='do')
        self.message = "Although not required by the 360Giving Standard, providing beneficiary data if available helps users to understand your data and allows it to be used in tools that visualise grants geographically."


class TitleDescriptionSame(AdditionalTest):
    def process(self, grant, path_prefix):
        title = grant.get("title")
        description = grant.get("description")
        if title and description and title == description:
            self.failed = True
            self.count += 1
            self.json_locations.append(path_prefix + '/description')

        self.heading = self.format_heading_count("a title and a description that are the same")
        self.message = "Users may find that the data is less useful as they are unable to discover more about the grants. Consider including a more detailed description if you have one."


class TitleLength(AdditionalTest):
    def process(self, grant, path_prefix):
        title = grant.get("title", '')
        if len(title) > 140:
            self.failed = True
            self.count += 1
            self.json_locations.append(path_prefix + '/title')

        self.heading = self.format_heading_count("a title longer than recommended")
        self.message = "Titles for grant activities should be under 140 characters long."


class OrganizationIdLooksInvalid(AdditionalTest):
    def process(self, grant, path_prefix):
        for org_type in ("fundingOrganization", "recipientOrganization"):
            orgs = grant.get(org_type, [])
            for num, org in enumerate(orgs):
                org_id = org.get('id')
                if not org_id:
                    continue
                id_location = '{}/{}/{}/id'.format(path_prefix, org_type, num)
                if org_id.upper().startswith('GB-CHC-'):
                    if not check_charity_number(org_id[7:]):
                        self.failed = True
                        self.json_locations.append(id_location)
                        self.count += 1
                elif org_id.upper().startswith('GB-COH-'):
                    if not check_company_number(org_id[7:]):
                        self.failed = True
                        self.json_locations.append(id_location)
                        self.count += 1

        self.heading = self.format_heading_count("funder or recipient organisation IDs that might not be valid")
        self.message = "The IDs might not be valid for the registration agency that they refer to - for example, a 'GB-CHC' ID that contains an invalid charity number. Common causes of this are missing leading digits, typos or incorrect values being entered into this field."


TEST_CLASSES = [
    ZeroAmountTest,
    RecipientOrg360GPrefix,
    FundingOrg360GPrefix,
    RecipientOrgUnrecognisedPrefix,
    FundingOrgUnrecognisedPrefix,
    RecipientOrgCharityNumber,
    RecipientOrgCompanyNumber,
    MoreThanOneFundingOrg,
    LooksLikeEmail,
    NoGrantProgramme,
    NoBeneficiaryLocation,
    TitleDescriptionSame,
    TitleLength,
    OrganizationIdLooksInvalid
]


def run_additional_checks(json_data, cell_source_map):
    if 'grants' not in json_data:
        return []
    test_instances = [test_cls(grants=json_data['grants']) for test_cls in TEST_CLASSES]

    for num, grant in enumerate(json_data['grants']):
        for test_instance in test_instances:
            test_instance.process(grant, 'grants/{}'.format(num))

    results = []

    for test_instance in test_instances:
        if not test_instance.failed:
            continue

        spreadsheet_locations = []
        if cell_source_map:
            try:
                spreadsheet_locations = [cell_source_map[location][0] for location in test_instance.json_locations]
            except KeyError:
                continue
        results.append((test_instance.produce_message(),
                        test_instance.json_locations,
                        spreadsheet_locations))
    return results
