import cove.lib.tools as tools
import requests
from collections import defaultdict
import json
import os


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
        'max_award_date': max_award_date,
        'min_award_date': min_award_date,
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
