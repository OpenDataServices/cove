from cove.lib.common import *


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
