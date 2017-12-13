import re
from collections import defaultdict, OrderedDict
from decimal import Decimal

import cove.lib.tools as tools
from cove.lib.common import common_checks_context, get_orgids_prefixes
from cove.lib.tools import datetime_or_date


orgids_prefixes = get_orgids_prefixes()
orgids_prefixes.append('360G')

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
            if amount_awarded and isinstance(amount_awarded, (int, Decimal, float)):
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


def common_checks_360(context, upload_dir, json_data, schema_obj):
    schema_name = schema_obj.release_pkg_schema_name
    checkers = {'date-time': (datetime_or_date, ValueError)}
    common_checks = common_checks_context(upload_dir, json_data, schema_obj, schema_name, context, extra_checkers=checkers)
    cell_source_map = common_checks['cell_source_map']
    additional_checks = run_additional_checks(json_data, cell_source_map, ignore_errors=True, return_on_error=None)

    context.update(common_checks['context'])
    context.update({
        'grants_aggregates': get_grants_aggregates(json_data, ignore_errors=True),
        'additional_checks_errored': additional_checks is None,
        'additional_checks': additional_checks,
        'additional_checks_count': (len(additional_checks) if additional_checks else 0) + (1 if context['data_only'] else 0),
        'common_error_types': ['uri', 'date-time', 'required', 'enum', 'integer', 'string']
    })

    return context


def get_prefixes(distinct_identifiers):

    org_identifier_prefixes = defaultdict(int)
    org_identifiers_unrecognised_prefixes = defaultdict(int)

    for org_identifier in distinct_identifiers:
        for prefix in orgids_prefixes:
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
    """Check if any grants have an amountAwarded of 0.

    Checks explicitly for a number with a value of 0"""

    check_text = {
        "heading": 'a value of £0',
        "message": "It’s worth taking a look at these grants and deciding if they should be published. It’s unusual to have grants of £0, but there may be a reasonable explanation. Additional information on why these grants are £0 might be useful to anyone using the data, so consider adding an explanation to the description of the grant."
    }

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

        self.heading = self.format_heading_count(self.check_text['heading'])
        self.message = self.check_text['message']


class RecipientOrg360GPrefix(AdditionalTest):
    """Check if any grants are using RecipientOrg IDs that start 360G or 360g"""

    check_text = {
        "heading": "a Recipient Org:Identifier that starts '360G-'",
        "message": "If the grant is to a recipient organisation that has an external identifier (such as a charity or company number), then this should be used instead. Using external identifiers helps people using your data to match it up against other data - for example to see who else has given grants to the same recipient, even if they’re known by a different name. If no external identifier can be used, then you can ignore this notice."
    }

    def process(self, grant, path_prefix):
        try:
            for num, organization in enumerate(grant['recipientOrganization']):
                if organization['id'].lower().startswith('360g'):
                    self.failed = True
                    self.json_locations.append(path_prefix + '/recipientOrganization/{}/id'.format(num))
                    self.count += 1
        except KeyError:
            pass

        self.heading = self.format_heading_count(self.check_text['heading'])
        self.message = self.check_text['message']


class FundingOrg360GPrefix(AdditionalTest):
    """Check if any grants are using FundingOrg IDs that start 360G or 360g"""

    check_text = {
        "heading": "a Funding Org:Identifier that starts '360G-'",
        "message": "If the grant is from a funding organisation that has an external identifier (such as a charity or company number), then this should be used instead. If no other identifier can be used, then you can ignore this notice."
    }

    def process(self, grant, path_prefix):
        try:
            for num, organization in enumerate(grant['fundingOrganization']):
                if organization['id'].lower().startswith('360g'):
                    self.failed = True
                    self.json_locations.append(path_prefix + '/fundingOrganization/{}/id'.format(num))
                    self.count += 1
        except KeyError:
            pass

        self.heading = self.format_heading_count(self.check_text['heading'])
        self.message = self.check_text['message']


class RecipientOrgUnrecognisedPrefix(AdditionalTest):
    """Check if any grants have RecipientOrg IDs that use a prefix that isn't on the Org ID prefix codelist"""

    check_text = {
        "heading": "a Recipient Org:Identifier that does not draw from a recognised register.",
        "message": "Using external identifiers (such as a charity or company number) helps people using your data to match it up against other data - for example to see who else has given grants to the same recipient, even if they’re known by a different name. If the data describes lots of grants to organisations that don’t have such identifiers, or grants to individuals, then you can ignore this notice."
    }

    def process(self, grant, path_prefix):
        try:
            count_failure = False
            for num, organization in enumerate(grant['recipientOrganization']):
                for prefix in orgids_prefixes:
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

        self.heading = self.format_heading_count(self.check_text['heading'])
        self.message = self.check_text['message']


class FundingOrgUnrecognisedPrefix(AdditionalTest):
    """Check if any grants have FundingOrg IDs that use a prefix that isn't on the Org ID prefix codelist"""

    check_text = {
        "heading": "a Funding Org:Identifier that does not draw from a recognised register.",
        "message": "Using external identifiers (such as a charity or company number) helps people using your data to match it up against other data - for example to see who else has given grants to the same recipient, even if they’re known by a different name. If the data describes lots of grants to organisations that don’t have such identifiers, or grants to individuals, then you can ignore this notice."
    }

    def process(self, grant, path_prefix):
        try:
            count_failure = False
            for num, organization in enumerate(grant['fundingOrganization']):
                for prefix in orgids_prefixes:
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

        self.heading = self.format_heading_count(self.check_text['heading'])
        self.message = self.check_text['message']


class RecipientOrgCharityNumber(AdditionalTest):
    """Check if any grants have RecipientOrg charity numbers that don't look like charity numbers

    Checks if the first two characters are letters, then checks that the remainder of the value is a number 6 or 7 digits long.
    """

    check_text = {
        "heading": "a value provided in the Recipient Org: Charity Number column that doesn’t look like a charity number",
        "message": "Common causes of this are missing leading digits, typos or incorrect values being entered into this field."
    }

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

        self.heading = self.format_heading_count(self.check_text['heading'])
        self.message = self.check_text['message']


class RecipientOrgCompanyNumber(AdditionalTest):
    """Checks if any grants have RecipientOrg company numbers that don't look like company numbers

    Checks if the value is 8 characters long, and that the last 6 of those characters are numbers
    """

    check_text = {
        "heading": "a value provided in the Recipient Org: Company Number column that doesn’t look like a company number",
        "message": "Common causes of this are missing leading digits, typos or incorrect values being entered into this field."
    }

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

        self.heading = self.format_heading_count(self.check_text['heading'])
        self.message = self.check_text['message']


class NoRecipientOrgCompanyCharityNumber(AdditionalTest):
    """Checks if any grants don't have either a Recipient Org:Company Number or Recipient Org:Charity Number"""

    check_text = {
        "heading": "not have either a Recipient Org:Company Number or a Recipient Org:Charity Number",
        "message": "Providing one or both of these, if possible, makes it easier for users to join up your data with other data sources to provide better insight into grantmaking. If your grants are to organisations that don’t have UK Company or UK Charity numbers, then you can ignore this notice."
    }

    def process(self, grant, path_prefix):
        try:
            count_failure = False
            for num, organization in enumerate(grant['recipientOrganization']):
                has_id_number = organization.get('companyNumber') or organization.get('charityNumber')
                if not has_id_number:
                    self.failed = True
                    count_failure = True
                    self.json_locations.append(path_prefix + '/recipientOrganization/{}/id'.format(num))

            if count_failure:
                self.count += 1
        except KeyError:
            pass

        self.heading = self.format_heading_count(self.check_text['heading'], verb="do")
        self.message = self.check_text['message']


class IncompleteRecipientOrg(AdditionalTest):
    """Checks if any grants lack one of either Recipient Org:Postal Code or both of Recipient Org:Location:Geographic Code and Recipient Org:Location:Geographic Code Type"""

    check_text = {
        "heading": "not have recipient organisation location information",
        "message": "Your data is missing information about the geographic location of recipient organisations; either Recipient Org:Postal Code or Recipient Org:Location:Geographic Code combined with Recipient Org:Location:Geographic Code Type. Knowing the geographic location of recipient organisations helps users to understand your data and allows it to be used in tools that visualise grants geographically."
    }

    def process(self, grant, path_prefix):
        try:
            count_failure = False
            for num, organization in enumerate(grant['recipientOrganization']):
                has_postal_code = organization.get('postalCode')
                has_location_data = organization.get('location') and any(
                    location.get('geoCode') and location.get('geoCodeType')
                    for location in organization.get('location')
                )

                complete_recipient_org_data = has_postal_code or has_location_data
                if not complete_recipient_org_data:
                    self.failed = True
                    count_failure = True
                    self.json_locations.append(path_prefix + '/recipientOrganization/{}/id'.format(num))
            if count_failure:
                self.count += 1
        except KeyError:
            pass

        self.heading = self.format_heading_count(self.check_text['heading'], verb="do")
        self.message = self.check_text['message']


class MoreThanOneFundingOrg(AdditionalTest):
    """Checks if the file contains multiple FundingOrganisation:IDs"""

    check_text = {
        "heading": "There are {} different funding organisation IDs listed",
        "message": "If you are expecting to be publishing data for multiple funders then you can ignore this notice. If you are only publishing for a single funder then you should review your Funding Organisation identifier column to see where multiple IDs have occurred."
    }

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

        self.heading = self.check_text["heading"].format(len(self.funding_organization_ids))
        self.message = self.check_text["message"]


compiled_email_re = re.compile('[\w.-]+@[\w.-]+\.[\w.-]+')


class LooksLikeEmail(AdditionalTest):
    """Checks if any grants contain text that looks like an email address

    The check looks for any number of alphanumerics, dots or hyphens, followed by an @ sign, followed by any number of alphanumerics, dots or hyphens, with a minimum of one dot after the @
    """

    check_text = {
        "heading": "text that looks like an email address",
        "message": "Your data may contain an email address (or something that looks like one), which can constitute personal data. The use and distribution of personal data is restricted by the Data Protection Act. You should ensure that any personal data is only included with the knowledge and consent of the person to whom it refers."
    }

    def process(self, grant, path_prefix):
        flattened_grant = OrderedDict(flatten_dict(grant))
        for key, value in flattened_grant.items():
            if isinstance(value, str) and compiled_email_re.search(value):
                self.failed = True
                self.json_locations.append(path_prefix + key)
                self.count += 1

        self.heading = self.format_heading_count(self.check_text['heading'], verb='contain')
        self.message = self.check_text['message']


class NoGrantProgramme(AdditionalTest):
    """Checks if any grants have no Grant Programme fields"""

    check_text = {
        "heading": "not contain any Grant Programme fields",
        "message": "Providing Grant Programme data, if available, helps users to better understand your data."
    }

    def process(self, grant, path_prefix):
        grant_programme = grant.get("grantProgramme")
        if not grant_programme:
            self.failed = True
            self.count += 1
            self.json_locations.append(path_prefix + '/id')

        self.heading = self.format_heading_count(self.check_text['heading'], verb='do')
        self.message = self.check_text['message']


class NoBeneficiaryLocation(AdditionalTest):
    """Checks if any grants have no Beneficiary Location fields"""

    check_text = {
        "heading": "not contain any beneficiary location fields",
        "message": "Providing beneficiary data, if available, helps users to understand which areas ultimately benefitted from the grant."
    }

    def process(self, grant, path_prefix):
        beneficiary_location = grant.get("beneficiaryLocation")
        if not beneficiary_location:
            self.failed = True
            self.count += 1
            self.json_locations.append(path_prefix + '/id')

        self.heading = self.format_heading_count(self.check_text['heading'], verb='do')
        self.message = self.check_text['message']


class TitleDescriptionSame(AdditionalTest):
    """Checks if any grants have the same text for Title and Description"""

    check_text = {
        "heading": "a title and a description that are the same",
        "message": "Users may find that the data is less useful as they are unable to discover more about the grants. Consider including a more detailed description if you have one."
    }

    def process(self, grant, path_prefix):
        title = grant.get("title")
        description = grant.get("description")
        if title and description and title == description:
            self.failed = True
            self.count += 1
            self.json_locations.append(path_prefix + '/description')

        self.heading = self.format_heading_count(self.check_text['heading'])
        self.message = self.check_text['message']


class TitleLength(AdditionalTest):
    """Checks if any grants have Titles longer than 140 characters"""

    check_text = {
        "heading": "a title longer than recommended",
        "message": "Titles for grant activities should be under 140 characters long."
    }

    def process(self, grant, path_prefix):
        title = grant.get("title", '')
        if len(title) > 140:
            self.failed = True
            self.count += 1
            self.json_locations.append(path_prefix + '/title')

        self.heading = self.format_heading_count(self.check_text['heading'])
        self.message = self.check_text['message']


class OrganizationIdLooksInvalid(AdditionalTest):
    """Checks if any grants have org IDs for fundingOrg or recipientOrg that don't look correctly formatted for their respective registration agency (eg GB-CHC- not looking like a valid company number)

    Looks at the start of the ID - if it's GB-CHC- or GB-COH-, performs the relevant format check
    """
 
    check_text = {
        "heading": "funder or recipient organisation IDs that might not be valid",
        "message": "The IDs might not be valid for the registration agency that they refer to - for example, a 'GB-CHC' ID that contains an invalid charity number. Common causes of this are missing leading digits, typos or incorrect values being entered into this field."
    }

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

        self.heading = self.format_heading_count(self.check_text['heading'])
        self.message = self.check_text['message']


class NoLastModified(AdditionalTest):
    """Check if any grants are missing Last Modified dates"""

    check_text = {
        "heading": "not have Last Modified information",
        "message": "Last Modified shows the date and time when information about a grant was last updated in your file. Including this information allows data users to see when changes have been made and reconcile differences between versions of your data. Please note: this is the date when the data was modified in your 360Giving file, rather than in any of your internal systems."
    }

    def process(self, grant, path_prefix):
        last_modified = grant.get("dateModified")
        if not last_modified:
            self.failed = True
            self.count += 1
            self.json_locations.append(path_prefix + '/id')

        self.heading = self.format_heading_count(self.check_text['heading'], verb='do')
        self.message = self.check_text['message']


class NoDataSource(AdditionalTest):
    """Checks if any grants are missing dataSource"""

    check_text = {
        "heading": "not have Data Source information",
        "message": "Data Source informs users about where information came from and is an important part of establishing trust in your data. This information should be a web link pointing to the source of this data, which may be an original 360Giving data file, a file from which the data was converted, or your organisation’s website."
    }

    def process(self, grant, path_prefix):
        data_source = grant.get("dataSource")
        if not data_source:
            self.failed = True
            self.count += 1
            self.json_locations.append(path_prefix + '/id')

        self.heading = self.format_heading_count(self.check_text['heading'], verb='do')
        self.message = self.check_text['message']


# class IncompleteBeneficiaryLocation(AdditionalTest):
#     """Checks if any grants that do have Beneficiary Location fields are missing any of the details"""

#     check_text = {
#         "heading": "incomplete beneficiary location information",
#         "message": "Your data is missing Beneficiary Location: Name, Beneficiary Location: Geographical Code and/or Beneficiary Location: Geographical Code Type. Beneficiary location information allows users of the data to understand who ultimately benefitted from the grant, not just the location of the organisation that provided the service. If your beneficiaries are in the same place as the organisation that the money went to, stating this is useful for anyone using your data as it cannot be inferred."
#     }

#     def process(self, grant, path_prefix):
#         beneficiary_location = grant.get("beneficiaryLocation")
#         if beneficiary_location:
#             for location_item in beneficiary_location:
#                 complete_beneficiary_data = location_item.get('name') and location_item.get('geoCode') and location_item.get('geoCodeType')
#                 if not complete_beneficiary_data:
#                     self.failed = True
#                     self.count += 1
#                     self.json_locations.append(path_prefix + '/beneficiaryLocation')
#                     break

#         self.heading = self.format_heading_count(self.check_text['heading'])
#         self.message = self.check_text["message"]


TEST_CLASSES = [
    ZeroAmountTest,
    RecipientOrg360GPrefix,
    FundingOrg360GPrefix,
    RecipientOrgUnrecognisedPrefix,
    FundingOrgUnrecognisedPrefix,
    RecipientOrgCharityNumber,
    RecipientOrgCompanyNumber,
    NoRecipientOrgCompanyCharityNumber,
    IncompleteRecipientOrg,
    MoreThanOneFundingOrg,
    LooksLikeEmail,
    NoGrantProgramme,
    NoBeneficiaryLocation,
    TitleDescriptionSame,
    TitleLength,
    OrganizationIdLooksInvalid,
    NoLastModified,
    NoDataSource,
    # IncompleteBeneficiaryLocation
]


@tools.ignore_errors
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
        spreadsheet_keys = ('sheet', 'letter', 'row_number', 'header')
        if cell_source_map:
            try:
                spreadsheet_locations = [dict(zip(spreadsheet_keys, cell_source_map[location][0]))
                                         for location in test_instance.json_locations]
            except KeyError:
                continue
        results.append((test_instance.produce_message(),
                        test_instance.json_locations,
                        spreadsheet_locations))
    return results
