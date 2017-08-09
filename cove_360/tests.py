import os

import pytest
from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.uploadedfile import UploadedFile

from . lib.schema import Schema360
from . lib.threesixtygiving import run_additional_checks
from cove.input.models import SuppliedData

# Source is cove_360/fixtures/WellcomeTrust-grants_fixed_2_grants.json
# see cove_360/fixtures/SOURCES for more info.
# Data has been edited to increase test coverage, so should not be used for
# anything besides testing.

GRANTS = {
    'grants': [{'Co-applicant(s)': 'Mr Bentley Crudgington, Mr Gary Thomas ',
                'Full name of applicant': 'Miss Abigail Addison',
                'Grant number': '105177/Z/14/Z',
                'Grant type': 'Large Arts Awards bob@bop.com',
                'Sponsor(s)': ' ',
                'Surname of applicant': 'Addison',
                'amountAwarded': 0,
                'awardDate': '24/07/2014',
                'currency': 'GBP',
                "beneficiaryLocation": [{
                    "name": "Bloomsbury",
                    "geoCodeType": "LONB"
                }],
                'dateModified': '13-03-2015',
                'fundingOrganization': [{'id': 'XSFAFA',
                                         'name': 'The Wellcome Trust'}],
                'id': '360G-wellcometrust-105177/Z/14/Z',
                'plannedDates': [{'duration': '30'}],
                'recipientOrganization': [{'addressLocality': 'London ',
                                           'charityNumber': '12345',
                                           'companyNumber': 'AAA',
                                           'id': '360G-Blah',
                                           'name': 'Animate Project Limited'}],
                'title': 'Silent Signal.  ,moo@moo.com '},
               {'Co-applicant(s)': ' ',
                'Department': 'Department of Museum Studies',
                'Full name of applicant': 'Prof Richard Sandell',
                'Grant number': '105182/Z/14/Z',
                'Grant type': 'Large Arts Awards',
                'Sponsor(s)': ' ',
                'Surname of applicant': 'Sandell',
                'amountAwarded': 178990,
                'awardDate': '24/07/2014',
                'currency': 'GBP',
                'dataSource': 'http://www.wellcome.ac.uk/Managing-a-grant/Grants-awarded/index.htm',

                'description': 'Exceptional and Extraordinary: unruly bodies and '
                               'minds in the medical museum. ',
                'fundingOrganization': [{'id': '360G-CHC-210183',
                                         'name': 'The Wellcome Trust'}],
                'grantProgramme': [{'code': 'AAC',
                                    'title': 'Arts Awards Funding Committee'}],
                'id': '360G-wellcometrust-105182/Z/14/Z',
                'plannedDates': [{'duration': '25'}],
                'recipientOrganization': [{'addressLocality': 'Leicester ',
                                           'location': [{
                                               'geoCodeType': 'UA',
                                               'name': 'Rhondda Cynon Taf',
                                               'geoCode': 'W06000016'}],
                                           'charityNumber': '1234567',
                                           'companyNumber': 'RC000659',
                                           'id': 'GB-UNKNOW-RC000659',
                                           'name': 'UNIVERSITY OF LEICESTER'}],
                'title': ('Exceptional and Extraordinary: unruly bodies and minds in the medical '
                          'museum - unique film, dance, performance and comedy commissions that draw '
                          'on museum collections to explore our problematic attitudes towards difference')},
               {'Co-applicant(s)': ' ',
                'Department': 'Department of Museum Studies',
                'Full name of applicant': 'Prof Richard Sandell',
                'Grant number': '105183/Z/14/Z',
                'Grant type': 'Large Arts Awards',
                'Sponsor(s)': ' ',
                'Surname of applicant': 'Sandell',
                'amountAwarded': 178990,
                'awardDate': '24/07/2014',
                'currency': 'GBP',
                "beneficiaryLocation": [{
                    "name": "Gateshed",
                    "geoCodeType": "MD",
                    "geoCode": "E08000037",
                    
                }],
                'dateModified': '13-03-2015',
                'description': 'Exceptional and Extraordinary: unruly bodies and '
                               'minds in the medical museum. ',
                'fundingOrganization': [{'id': 'GB-COH-A106590',
                                         'name': 'The Wellcome Trust'}],
                'grantProgramme': [{'code': 'AAC',
                                    'title': 'Arts Awards Funding Committee'}],
                'id': '360G-wellcometrust-105183/Z/14/Z',
                'plannedDates': [{'duration': '25'}],
                'recipientOrganization': [{'addressLocality': 'Leicester ',
                                           'id': 'GB-CHC-10659',
                                           'name': 'UNIVERSITY OF LEICESTER'}],
                'relatedActivity': ["", "360G-xxx"],
                'title': 'Exceptional and Extraordinary: unruly bodies and minds '
                         'in the medical museum. '}]}

SOURCE_MAP = {
    'grants/0': [['grants', 2]],
    'grants/0/Co-applicant(s)': [['grants', 'E', 2, 'Co-applicant(s)']],
    'grants/0/Full name of applicant': [['grants',
                                         'D',
                                         2,
                                         'Full name of applicant']],
    'grants/0/Grant number': [['grants', 'B', 2, 'Grant number']],
    'grants/0/Grant type': [['grants', 'G', 2, 'Grant type']],
    'grants/0/Sponsor(s)': [['grants', 'F', 2, 'Sponsor(s)']],
    'grants/0/Surname of applicant': [['grants', 'C', 2, 'Surname of applicant']],
    'grants/0/amountAwarded': [['grants', 'Q', 2, 'Amount Awarded']],
    'grants/0/awardDate': [['grants', 'S', 2, 'Award Date']],
    'grants/0/currency': [['grants', 'R', 2, 'Currency']],
    'grants/0/beneficiaryLocation': [['grants', 'AA', 2, 'Beneficiary Location']],
    'grants/0/dataSource': [['grants', 'Y', 2, 'Data source']],
    'grants/0/dateModified': [['grants', 'X', 2, 'Last modified']],
    'grants/0/fundingOrganization/0': [['grants', 2]],
    'grants/0/fundingOrganization/0/id': [['grants',
                                           'V',
                                           2,
                                           'Funding Org:Identifier']],
    'grants/0/fundingOrganization/0/name': [['grants',
                                             'W',
                                             2,
                                             'Funding Org:Name']],
    'grants/0/id': [['grants', 'A', 2, 'Identifier']],
    'grants/0/plannedDates/0': [['grants', 2]],
    'grants/0/plannedDates/0/duration': [['grants',
                                          'P',
                                          2,
                                          'Planned Dates:Duration (months)']],
    'grants/0/recipientOrganization/0': [['grants', 2]],
    'grants/0/recipientOrganization/0/addressLocality': [['grants',
                                                          'N',
                                                          2,
                                                          'Recipient Org:City']],
    'grants/0/recipientOrganization/0/charityNumber': [['grants',
                                                        'M',
                                                        2,
                                                        'Recipient Org:Charity '
                                                        'Number']],
    'grants/0/recipientOrganization/0/companyNumber': [['grants',
                                                        'L',
                                                        2,
                                                        'Recipient Org:Company '
                                                        'Number']],
    'grants/0/recipientOrganization/0/id': [['grants',
                                             'J',
                                             2,
                                             'Recipient Org:Identifier']],
    'grants/0/recipientOrganization/0/name': [['grants',
                                               'K',
                                               2,
                                               'Recipient Org:Name']],
    'grants/0/title': [['grants', 'O', 2, 'Title']],
    'grants/1': [['grants', 3]],
    'grants/1/Co-applicant(s)': [['grants', 'E', 3, 'Co-applicant(s)']],
    'grants/1/Department': [['grants', 'H', 3, 'Department']],
    'grants/1/Full name of applicant': [['grants',
                                         'D',
                                         3,
                                         'Full name of applicant']],
    'grants/1/Grant number': [['grants', 'B', 3, 'Grant number']],
    'grants/1/Grant type': [['grants', 'G', 3, 'Grant type']],
    'grants/1/Sponsor(s)': [['grants', 'F', 3, 'Sponsor(s)']],
    'grants/1/Surname of applicant': [['grants', 'C', 3, 'Surname of applicant']],
    'grants/1/amountAwarded': [['grants', 'Q', 3, 'Amount Awarded']],
    'grants/1/awardDate': [['grants', 'S', 3, 'Award Date']],
    'grants/1/currency': [['grants', 'R', 3, 'Currency']],
    'grants/1/dataSource': [['grants', 'Y', 3, 'Data source']],
    'grants/1/dateModified': [['grants', 'X', 3, 'Last modified']],
    'grants/1/description': [['grants', 'Z', 3, 'Description']],
    'grants/1/fundingOrganization/0': [['grants', 3]],
    'grants/1/fundingOrganization/0/id': [['grants',
                                           'V',
                                           3,
                                           'Funding Org:Identifier']],
    'grants/1/fundingOrganization/0/name': [['grants',
                                             'W',
                                             3,
                                             'Funding Org:Name']],
    'grants/1/grantProgramme/0': [['grants', 3]],
    'grants/1/grantProgramme/0/code': [['grants', 'T', 3, 'Grant Programme:Code']],
    'grants/1/grantProgramme/0/title': [['grants',
                                         'U',
                                         3,
                                         'Grant Programme:Title']],
    'grants/1/id': [['grants', 'A', 3, 'Identifier']],
    'grants/1/plannedDates/0': [['grants', 3]],
    'grants/1/plannedDates/0/duration': [['grants',
                                          'P',
                                          3,
                                          'Planned Dates:Duration (months)']],
    'grants/1/recipientOrganization/0': [['grants', 3]],
    'grants/1/recipientOrganization/0/addressLocality': [['grants',
                                                          'N',
                                                          3,
                                                          'Recipient Org:City']],
    'grants/1/recipientOrganization/0/charityNumber': [['grants',
                                                        'M',
                                                        3,
                                                        'Recipient Org:Charity '
                                                        'Number']],
    'grants/1/recipientOrganization/0/companyNumber': [['grants',
                                                        'L',
                                                        3,
                                                        'Recipient Org:Company '
                                                        'Number']],
    'grants/1/recipientOrganization/0/id': [['grants',
                                             'J',
                                             3,
                                             'Recipient Org:Identifier']],
    'grants/1/recipientOrganization/0/name': [['grants',
                                               'K',
                                               3,
                                               'Recipient Org:Name']],
    'grants/1/title': [['grants', 'O', 3, 'Title']],
    'grants/2': [['grants', 4]],
    'grants/2/Co-applicant(s)': [['grants', 'E', 4, 'Co-applicant(s)']],
    'grants/2/Department': [['grants', 'H', 4, 'Department']],
    'grants/2/Full name of applicant': [['grants',
                                         'D',
                                         4,
                                         'Full name of applicant']],
    'grants/2/Grant number': [['grants', 'B', 4, 'Grant number']],
    'grants/2/Grant type': [['grants', 'G', 4, 'Grant type']],
    'grants/2/Sponsor(s)': [['grants', 'F', 4, 'Sponsor(s)']],
    'grants/2/Surname of applicant': [['grants', 'C', 4, 'Surname of applicant']],
    'grants/2/amountAwarded': [['grants', 'Q', 4, 'Amount Awarded']],
    'grants/2/awardDate': [['grants', 'S', 4, 'Award Date']],
    'grants/2/currency': [['grants', 'R', 4, 'Currency']],
    'grants/2/dataSource': [['grants', 'Y', 4, 'Data source']],
    'grants/2/dateModified': [['grants', 'X', 4, 'Last modified']],
    'grants/2/description': [['grants', 'Z', 4, 'Description']],
    'grants/2/fundingOrganization/0': [['grants', 4]],
    'grants/2/fundingOrganization/0/id': [['grants',
                                           'V',
                                           4,
                                           'Funding Org:Identifier']],
    'grants/2/fundingOrganization/0/name': [['grants',
                                             'W',
                                             4,
                                             'Funding Org:Name']],
    'grants/2/grantProgramme/0': [['grants', 4]],
    'grants/2/grantProgramme/0/code': [['grants', 'T', 4, 'Grant Programme:Code']],
    'grants/2/grantProgramme/0/title': [['grants',
                                         'U',
                                         4,
                                         'Grant Programme:Title']],
    'grants/2/id': [['grants', 'A', 4, 'Identifier']],
    'grants/2/plannedDates/0': [['grants', 4]],
    'grants/2/plannedDates/0/duration': [['grants',
                                          'P',
                                          4,
                                          'Planned Dates:Duration (months)']],
    'grants/2/recipientOrganization/0': [['grants', 4]],
    'grants/2/recipientOrganization/0/addressLocality': [['grants',
                                                          'N',
                                                          4,
                                                          'Recipient Org:City']],
    'grants/2/recipientOrganization/0/charityNumber': [['grants',
                                                        'M',
                                                        4,
                                                        'Recipient Org:Charity '
                                                        'Number']],
    'grants/2/recipientOrganization/0/companyNumber': [['grants',
                                                        'L',
                                                        4,
                                                        'Recipient Org:Company '
                                                        'Number']],
    'grants/2/recipientOrganization/0/id': [['grants',
                                             'J',
                                             4,
                                             'Recipient Org:Identifier']],
    'grants/2/recipientOrganization/0/name': [['grants',
                                               'K',
                                               4,
                                               'Recipient Org:Name']],
    'grants/2/title': [['grants', 'O', 4, 'Title']]
}


RESULTS = [
    ({'heading': "1 grant has a value of £0",
      'message': ("It’s worth taking a look at these grants and deciding if "
                  "they should be published. It’s unusual to have grants of £0, but "
                  "there may be a reasonable explanation. Additional information "
                  "on why these grants are £0 might be useful to anyone using the data, "
                  "so consider adding an explanation to the description of the grant.")},
     ['grants/0/amountAwarded'],
     [['grants', 'Q', 2, 'Amount Awarded']]),
    ({'heading': "1 grant has a Recipient Org:Identifier that starts '360G-'",
      'message': ("If the grant is from a recipient organisation that has an external "
                  "identifier (such as a charity number, company number, or in the case "
                  "of local authorities, geocodes), then this should be used instead. If "
                  "no other identifier can be used, then this notice can be ignored.")},
     ['grants/0/recipientOrganization/0/id'],
     [['grants', 'J', 2, 'Recipient Org:Identifier']]),
    ({'heading': "1 grant has a Funding Org:Identifier that starts '360G-'",
      'message': ("If the grant is from a recipient organisation that has an external "
                  "identifier (such as a charity number, company number, or in the "
                  "case of local authorities, geocodes), then this should be used instead. If "
                  "no other identifier can be used, then this notice can be ignored.")},
     ['grants/1/fundingOrganization/0/id'],
     [['grants', 'V', 3, 'Funding Org:Identifier']]),
    ({'heading': ("1 grant has a Recipient Org:Identifier that doesn’t draw from "
                  "an external identification body"),
      'message': ("Using external identifiers (e.g. a charity number or a company number) "
                  "helps people using your data to match it up against other data - for "
                  "example to see who else has given grants to the same recipient, even "
                  "if they’re known by a different name. If the data describes lots of "
                  "grants to organisations that don’t have such identifiers or individuals "
                  "then you can ignore this notice.")},
     ['grants/1/recipientOrganization/0/id'],
     [['grants', 'J', 3, 'Recipient Org:Identifier']]),
    ({'heading': ("1 grant has a Funding Org:Identifier that doesn’t draw from "
                  "an external identification body"),
      'message': ("Using external identifiers (e.g. a charity number or a company number) "
                  "helps people using your data to match it up against other data - for "
                  "example to see who else has given grants to the same recipient, even "
                  "if they’re known by a different name. If the data describes lots of "
                  "grants to organisations that don’t have such identifiers or individuals "
                  "then you can ignore this notice.")},
     ['grants/0/fundingOrganization/0/id'],
     [['grants', 'V', 2, 'Funding Org:Identifier']]),
    ({'heading': ("1 grant has a value provided in the Recipient Org: Charity Number column "
                 "that doesn’t look like a charity number"),
      'message': ("Common causes of this are missing leading digits, typos or incorrect "
                  "values being entered into this field.")},
     ['grants/0/recipientOrganization/0/charityNumber'],
     [['grants', 'M', 2, 'Recipient Org:Charity Number']]),
    ({'heading': ("1 grant has a value provided in the Recipient Org: Company Number column "
                  "that doesn’t look like a company number"),
      'message': ("Common causes of this are missing leading digits, typos or incorrect "
                  "values being entered into this field.")},
     ['grants/0/recipientOrganization/0/companyNumber'],
     [['grants', 'L', 2, 'Recipient Org:Company Number']]),
    ({'heading': "1 grant does not have either a Recipient Org:Company Number or a Recipient Org:Charity Number",
      'message': ("Providing one or both of these, if possible, makes it easier for users of "
                  "your data to join up the data with other data sources to provide better "
                  "insight into grant-making. You don’t need to do anything if your grants are "
                  "to organisations that don’t have UK Company or UK Charity numbers.")},
     ['grants/2/recipientOrganization/0/id'],
     [['grants', 'J', 4, 'Recipient Org:Identifier']]),
    ({'heading': "3 grants have incomplete recipient organisation information",
      'message': ("Your data is missing Recipient Org: Postal Code, Recipient Org: Location:Geographic "
                  "Code or Recipient Org: Location: Geographic Code Type. Knowing the geographic location "
                  "of recipient organisations allows users of your data to understand your data and combine "
                  "it with other data sets to form a broader picture of grant-making.")},
     ['grants/0/recipientOrganization/0/id', 'grants/1/recipientOrganization/0/id', 'grants/2/recipientOrganization/0/id'],
     [['grants', 'J', 2, 'Recipient Org:Identifier'], ['grants', 'J', 3, 'Recipient Org:Identifier'],
      ['grants', 'J', 4, 'Recipient Org:Identifier']]),
    ({'heading': "There are 3 different funding organisation IDs listed",
      'message': ("If you are expecting to be publishing data for multiple funders then "
                  "this notice can be ignored, however if you are only publishing for a "
                  "single funder then you should review your Funder ID column to see where "
                  "multiple IDs have occurred.")},
     ['grants/0/fundingOrganization/0/id', 'grants/1/fundingOrganization/0/id', 'grants/2/fundingOrganization/0/id'],
     [['grants', 'V', 2, 'Funding Org:Identifier'],
      ['grants', 'V', 3, 'Funding Org:Identifier'],
      ['grants', 'V', 4, 'Funding Org:Identifier']]),
    ({'heading': "2 grants contain text that looks like an email address",
      'message': ("This may indicate that the data contains personal data, use and "
                  "distribution of which is restricted by the Data Protection Act. You "
                  "should ensure that any personal data is included with the knowledge "
                  "and consent of the person to whom it refers.")},
     ['grants/0/Grant type', 'grants/0/title'],
     [['grants', 'G', 2, 'Grant type'], ['grants', 'O', 2, 'Title']]),
    ({'heading': "1 grant does not contain any Grant Programme fields",
     'message': ("Although not required by the 360Giving Standard, providing Grant "
                 "Programme data if available helps users to better understand your data.")},
     ['grants/0/id'],
     [['grants', 'A', 2, 'Identifier']]),
    ({'heading': "1 grant does not contain any beneficiary location fields",
      'message': ("Although not required by the 360Giving Standard, providing beneficiary "
                  "data if available helps users to understand your data and allows it to be "
                  "used in tools that visualise grants geographically.")},
     ['grants/1/id'],
     [['grants', 'A', 3, 'Identifier']]),
    ({'heading': "1 grant has incomplete beneficiary location information",
      'message': ("Your data is missing Beneficiary Location: Name, Beneficiary Location: "
                  "Geographical Code and/or Beneficiary Location: Geographical Code Type. "
                  "Beneficiary location information allows users of the data to understand who "
                  "ultimately benefitted from the grant, not just the location of the organisation "
                  "that provided the service. If your beneficiaries are in the same place as the "
                  "organisation that the money went to, stating this is useful for anyone using your "
                  "data as it cannot be inferred.")},
     ['grants/0/beneficiaryLocation'],
     [['grants', 'AA', 2, 'Beneficiary Location']]),
    ({'heading': "1 grant has a title and a description that are the same",
      'message': ("Users may find that the data is less useful as they are unable to "
                  "discover more about the grants. Consider including a more detailed "
                  "description if you have one.")},
     ['grants/2/description'],
     [['grants', 'Z', 4, 'Description']]),
    ({'heading': "1 grant has a title longer than recommended",
      'message': "Titles for grant activities should be under 140 characters long."},
     ['grants/1/title'],
     [['grants', 'O', 3, 'Title']]),
    ({'heading': "2 grants have funder or recipient organisation IDs that might not be valid",
      'message': ("The IDs might not be valid for the registration agency that they refer to "
                  "- for example, a 'GB-CHC' ID that contains an invalid charity number. Common "
                  "causes of this are missing leading digits, typos or incorrect values being "
                  "entered into this field.")},
     ['grants/2/fundingOrganization/0/id', 'grants/2/recipientOrganization/0/id'],
     [['grants', 'V', 4, 'Funding Org:Identifier'],
      ['grants', 'J', 4, 'Recipient Org:Identifier']]),
    ({'heading': "1 grant does not have a Last Modified date",
      'message': "Last Modified allows data users to reconcile discrepancies between versions of your data."},
     ['grants/1/id'],
     [['grants', 'A', 3, 'Identifier']]),
    ({'heading': "2 grants do not have a Data Source field",
      'message': "Knowing where information came from is an important part of establishing trust in your data."},
     ['grants/0/id', 'grants/2/id'],
     [['grants', 'A', 2, 'Identifier'], ['grants', 'A', 4, 'Identifier']]),
    ({'heading': "3 grants do not have a Classification: Title field",
      'message': ("This field allows you to describe how you classify the grant or have tagged it internally. "
                  "Examples include classifying by sector (eg Healthcare) or target group (eg NEET).")},
     ['grants/0/id', 'grants/1/id', 'grants/2/id'],
     [['grants', 'A', 2, 'Identifier'], ['grants', 'A', 3, 'Identifier'], ['grants', 'A', 4, 'Identifier']])
]


@pytest.mark.parametrize('json_data', [
    # A selection of JSON strings we expect to give a 200 status code, even
    # though some of them aren't valid OCDS
    'true',
    'null',
    '1',
    '{}',
    '[]',
    '[[]]',
    '{"grants": {}}',
    '{"grants" : 1.0}',
    '{"grants" : 2}',
    '{"grants" : true}',
    '{"grants" : "test"}',
    '{"grants" : null}',
    '{"grants" : {"a":"b"}}',
    '{"grants" : [["test"]]}',
])
@pytest.mark.django_db
def test_explore_page(client, json_data):
    data = SuppliedData.objects.create()
    data.original_file.save('test.json', ContentFile(json_data))
    data.current_app = 'cove_360'
    resp = client.get(data.get_absolute_url())
    assert resp.status_code == 200


@pytest.mark.django_db
def test_explore_page_convert(client):
    data = SuppliedData.objects.create()
    data.original_file.save('test.json', ContentFile('{}'))
    data.current_app = 'cove_360'
    resp = client.get(data.get_absolute_url())
    assert resp.status_code == 200
    assert resp.context['conversion'] == 'flattenable'

    # Check that what the repr of our SuppliedData object looks like
    assert 'SuppliedData' in repr(data)
    assert 'test.json' in repr(data)

    resp = client.post(data.get_absolute_url(), {'flatten': 'true'})
    assert resp.status_code == 200
    assert resp.context['conversion'] == 'flatten'
    assert 'converted_file_size' in resp.context
    assert 'converted_file_size_titles' in resp.context


@pytest.mark.django_db
def test_explore_page_csv(client):
    data = SuppliedData.objects.create()
    data.original_file.save('test.csv', ContentFile('a,b'))
    resp = client.get(data.get_absolute_url())
    assert resp.status_code == 200
    assert resp.context['conversion'] == 'unflatten'
    assert resp.context['converted_file_size'] == 20


@pytest.mark.django_db
def test_explore_not_json(client):
    data = SuppliedData.objects.create()
    with open(os.path.join('cove_360', 'fixtures', 'WellcomeTrust-grants_malformed.json')) as fp:
        data.original_file.save('test.json', UploadedFile(fp))
    resp = client.get(data.get_absolute_url())
    assert resp.status_code == 200
    assert b'not well formed JSON' in resp.content


@pytest.mark.django_db
def test_explore_unconvertable_spreadsheet(client):
    data = SuppliedData.objects.create()
    with open(os.path.join('cove', 'fixtures', 'bad.xlsx'), 'rb') as fp:
        data.original_file.save('basic.xlsx', UploadedFile(fp))
    resp = client.get(data.get_absolute_url())
    assert resp.status_code == 200
    assert b'We think you tried to supply a spreadsheet, but we failed to convert it to JSON.' in resp.content


@pytest.mark.django_db
def test_explore_unconvertable_json(client):
    data = SuppliedData.objects.create()
    with open(os.path.join('cove_360', 'fixtures', 'unconvertable_json.json')) as fp:
        data.original_file.save('unconvertable_json.json', UploadedFile(fp))
    resp = client.post(data.get_absolute_url(), {'flatten': 'true'})
    assert resp.status_code == 200
    assert b'could not be converted' in resp.content


def test_schema_360():
    schema = Schema360()
    assert schema.release_schema_name == settings.COVE_CONFIG['schema_item_name']
    assert schema.release_pkg_schema_name == settings.COVE_CONFIG['schema_name']
    assert schema.schema_host == settings.COVE_CONFIG['schema_host']
    assert schema.release_schema_url == settings.COVE_CONFIG['schema_host'] + settings.COVE_CONFIG['schema_item_name']
    assert schema.release_pkg_schema_url == settings.COVE_CONFIG['schema_host'] + settings.COVE_CONFIG['schema_name']


def test_additional_checks():
    assert run_additional_checks(GRANTS, SOURCE_MAP) == RESULTS
