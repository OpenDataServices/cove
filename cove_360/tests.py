import os

import pytest
from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.uploadedfile import UploadedFile

from . lib.schema import Schema360
from . lib.threesixtygiving import run_extra_checks, extend_numbers, TEST_CLASSES
from cove.input.models import SuppliedData

# Source is cove_360/fixtures/fundingproviders-grants_fixed_2_grants.json
# see cove_360/fixtures/SOURCES for more info.
# Data has been edited to increase test coverage, so should not be used for
# anything besides testing.

GRANTS = {
    'grants': [{'Co-applicant(s)': 'Miss Hypatia Alexandria, Mr Thomas Aquinas',
                'Full name of applicant': 'Miss Jane Roe',
                'Grant number': '000001/X/00/X',
                'Grant type': 'Large Awards bob@bop.com',
                'Sponsor(s)': ' ',
                'Surname of applicant': 'Roe',
                'amountAwarded': 0,
                'awardDate': '24/07/2014',
                'currency': 'GBP',
                "beneficiaryLocation": [{
                    "name": "Bloomsbury",
                    "geoCodeType": "LONB"
                }],
                'dateModified': '13-03-2015',
                'fundingOrganization': [{'id': 'XSFAFA',
                                         'name': 'Funding Providers UK'}],
                'id': '360G-fundingproviders-000001/X/00/X',
                'plannedDates': [{'duration': '30'}],
                'recipientOrganization': [{'addressLocality': 'London',
                                           'location': [{
                                               'name': 'Somewhere in London',
                                               'geoCode': 'W06000016'}],
                                           'charityNumber': '12345',
                                           'companyNumber': 'AAA',
                                           'id': '360G-Blah',
                                           'name': 'Company Name Limited'}],
                'classifications': [{
                    'title': 'Classification title'}],
                'title': 'Title A.  ,moo@moo.com '},
               {'Co-applicant(s)': ' ',
                'Department': 'Department of Studies',
                'Full name of applicant': 'Prof John Doe',
                'Grant number': '000002/X/00/X',
                'Grant type': 'Large Awards',
                'Sponsor(s)': ' ',
                'Surname of applicant': 'Doe',
                'amountAwarded': 178990,
                'awardDate': '24/07/2014',
                'currency': 'GBP',
                'dataSource': 'http://www.fundingproviders.co.uk/grants/',

                'description': 'Description for project A',
                'fundingOrganization': [{'id': '360G-CHC-000001',
                                         'name': 'Funding Providers UK'}],
                'grantProgramme': [{'code': 'AAC',
                                    'title': 'Awards Funding Committee'}],
                'id': '360G-fundingproviders-000002/X/00/X',
                'plannedDates': [{'duration': '25'}],
                'recipientOrganization': [{'addressLocality': 'Leicester ',
                                           'location': [{
                                               'geoCodeType': 'UA',
                                               'name': 'Rhondda Cynon Taf',
                                               'geoCode': 'W06000016'}],
                                           'charityNumber': '1234567',
                                           'companyNumber': 'RC000000',
                                           'id': 'GB-UNKNOW-RC000000',
                                           'name': 'University of UK'}],
                'title': ('Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do '
                          'eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut '
                          'enim ad minim veniam, quis nostrud exercitation ullamco laboris.')},
               {'Co-applicant(s)': ' ',
                'Department': 'Department of Studies',
                'Full name of applicant': 'Prof John Doe',
                'Grant number': '00002/X/00/X',
                'Grant type': 'Large Awards',
                'Sponsor(s)': ' ',
                'Surname of applicant': 'Doe',
                'amountAwarded': 178990,
                'awardDate': '24/07/2014',
                'currency': 'GBP',
                "beneficiaryLocation": [{
                    "name": "Gateshed",
                    "geoCodeType": "MD",
                    "geoCode": "E08000037",
                    
                }],
                'dateModified': '13-03-2015',
                'description': 'Excepteur sint occaecat cupidatat non proident, sunt in culpa '
                               'qui officia deserunt mollit anim id est laborum.',
                'fundingOrganization': [{'id': 'GB-COH-000000',
                                         'name': 'Funding Providers UK'}],
                'grantProgramme': [{'code': 'AAC',
                                    'title': 'Arts Awards Funding Committee'}],
                'id': '360G-fundingproviders-000003/X/00/X',
                'plannedDates': [{'duration': '25'}],
                'recipientOrganization': [{'addressLocality': 'Leicester ',
                                           'id': 'GB-CHC-00001',
                                           'name': 'University of UK',
                                           'postalCode': 'SW10 0AB'}],
                'relatedActivity': ["", "360G-xxx"],
                'title': 'Excepteur sint occaecat cupidatat non proident, sunt in culpa '
                         'qui officia deserunt mollit anim id est laborum.'}]}


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


ADDITIONAL_CHECKS_RESULTS = [
    ({'heading': "33% of grants do not have recipient organisation location information",
      'message': ("Your data is missing information about the geographic location of recipient "
                  "organisations; either <span class=\"highlight-background-text\">Recipient Org:Postal Code</span> "
                  "or <span class=\"highlight-background-text\">Recipient Org:Location:Geographic Code</span> combined "
                  "with <span class=\"highlight-background-text\">Recipient Org:Location:Geographic Code Type</span>. "
                  "Knowing the geographic location of recipient organisations helps users to understand your data and "
                  "allows it to be used in tools that visualise grants geographically.")},
     ['grants/0/recipientOrganization/0/id'],
     [{'sheet': 'grants', 'letter': 'J', 'row_number': 2, 'header': 'Recipient Org:Identifier'}]),
    ({'heading': "67% of grants contain text that looks like an email address",
      'message': ("Your data may contain an email address (or something that looks like one), "
                  "which can constitute personal data. The use and distribution of personal data "
                  "is restricted by the Data Protection Act. You should ensure that any personal "
                  "data is only included with the knowledge and consent of the person to whom it refers.")},
     ['grants/0/Grant type', 'grants/0/title'],
     [{'sheet': 'grants', 'letter': 'G', 'row_number': 2, 'header': 'Grant type'},
      {'sheet': 'grants', 'letter': 'O', 'row_number': 2, 'header': 'Title'}]),
    ({'heading': ("33% of grants do not contain any <span class=\"highlight-background-text\">Grant Programme</span> "
                  "fields"),
     'message': ("Providing <span class=\"highlight-background-text\">Grant Programme</span> data, if available, helps "
                 "users to better understand your data.")},
     ['grants/0/id'],
     [{'sheet': 'grants', 'letter': 'A', 'row_number': 2, 'header': 'Identifier'}]),
    ({'heading': "33% of grants do not contain any beneficiary location fields",
      'message': ("Providing beneficiary data, if available, helps users to "
                  "understand which areas ultimately benefitted from the grant.")},
     ['grants/1/id'],
     [{'sheet': 'grants', 'letter': 'A', 'row_number': 3, 'header': 'Identifier'}]),
    # ({'heading': "1 grant has incomplete beneficiary location information",
    #   'message': ("Your data is missing Beneficiary Location: Name, Beneficiary Location: "
    #               "Geographical Code and/or Beneficiary Location: Geographical Code Type. "
    #               "Beneficiary location information allows users of the data to understand who "
    #               "ultimately benefitted from the grant, not just the location of the organisation "
    #               "that provided the service. If your beneficiaries are in the same place as the "
    #               "organisation that the money went to, stating this is useful for anyone using your "
    #               "data as it cannot be inferred.")},
    #  ['grants/0/beneficiaryLocation'],
    #  [{'sheet': 'grants', 'letter': 'AA', 'row_number': 2, 'header': 'Beneficiary Location'}]),
    ({'heading': "33% of grants have a title and a description that are the same",
      'message': ("Users may find that the data is less useful as they are unable to "
                  "discover more about the grants. Consider including a more detailed "
                  "description if you have one.")},
     ['grants/2/description'],
     [{'sheet': 'grants', 'letter': 'Z', 'row_number': 4, 'header': 'Description'}]),
    ({'heading': "33% of grants have a title longer than recommended",
      'message': "Titles for grant activities should be under 140 characters long."},
     ['grants/1/title'],
     [{'sheet': 'grants', 'letter': 'O', 'row_number': 3, 'header': 'Title'}]),
    ({'heading': "67% of grants have funder or recipient organisation IDs that might not be valid",
      'message': ("The IDs might not be valid for the registration agency that they refer to "
                  "- for example, a 'GB-CHC' ID that contains an invalid charity number. Common "
                  "causes of this are missing leading digits, typos or incorrect values being "
                  "entered into this field.")},
     ['grants/2/fundingOrganization/0/id', 'grants/2/recipientOrganization/0/id'],
     [{'sheet': 'grants', 'letter': 'V', 'row_number': 4, 'header': 'Funding Org:Identifier'},
      {'sheet': 'grants', 'letter': 'J', 'row_number': 4, 'header': 'Recipient Org:Identifier'}])
]


QUALITY_ACCURACY_CHECKS_RESULTS = [
    ({'heading': "33% of grants have a value of £0",
      'message': ("It’s worth taking a look at these grants and deciding if "
                  "they should be published. It’s unusual to have grants of £0, but "
                  "there may be a reasonable explanation. Additional information "
                  "on why these grants are £0 might be useful to anyone using the data, "
                  "so consider adding an explanation to the description of the grant.")},
     ['grants/0/amountAwarded'],
     [{'sheet': 'grants', 'letter': 'Q', 'row_number': 2, 'header': 'Amount Awarded'}]),
    ({'heading': ("33% of grants have a <span class=\"highlight-background-text\">Funding Org:Identifier</span> that "
                  "does not draw from a recognised register."),
      'message': ("Using external identifiers (such as a charity or company number) helps "
                  "people using your data to match it up against other data - for example "
                  "to see who else has given grants to the same recipient, even if they’re "
                  "known by a different name. If the data describes lots of grants to "
                  "organisations that don’t have such identifiers, or grants to individuals, "
                  "then you can ignore this notice.")},
     ['grants/0/fundingOrganization/0/id'],
     [{'sheet': 'grants', 'letter': 'V', 'row_number': 2, 'header': 'Funding Org:Identifier'}]),
    ({'heading': ("33% of grants have a <span class=\"highlight-background-text\">Recipient Org:Identifier</span> that "
                  "does not draw from a recognised register."),
      'message': ("Using external identifiers (such as a charity or company number) helps "
                  "people using your data to match it up against other data - for example "
                  "to see who else has given grants to the same recipient, even if they’re "
                  "known by a different name. If the data describes lots of grants to "
                  "organisations that don’t have such identifiers, or grants to individuals, "
                  "then you can ignore this notice.")},
     ['grants/1/recipientOrganization/0/id'],
     [{'sheet': 'grants', 'letter': 'J', 'row_number': 3, 'header': 'Recipient Org:Identifier'}]),
    ({'heading': ("33% of grants have a value provided in the "
                  "<span class=\"highlight-background-text\">Recipient Org: Charity Number</span> column "
                  "that doesn’t look like a charity number"),
      'message': ("Common causes of this are missing leading digits, typos or incorrect "
                  "values being entered into this field.")},
     ['grants/0/recipientOrganization/0/charityNumber'],
     [{'sheet': 'grants', 'letter': 'M', 'row_number': 2, 'header': 'Recipient Org:Charity Number'}]),
    ({'heading': ("33% of grants have a value provided in the "
                  "<span class=\"highlight-background-text\">Recipient Org: Company Number</span> column "
                  "that doesn’t look like a company number"),
      'message': ("Common causes of this are missing leading digits, typos or incorrect "
                  "values being entered into this field. Company numbers are typically 8 digits, possibly starting SC, "
                  "for example <span class=\"highlight-background-text\">SC01234569</span> or "
                  "<span class=\"highlight-background-text\">09876543</span>. You can check company numbers online "
                  "at <a href=\"https://beta.companieshouse.gov.uk/\">Companies House")},
     ['grants/0/recipientOrganization/0/companyNumber'],
     [{'sheet': 'grants', 'letter': 'L', 'row_number': 2, 'header': 'Recipient Org:Company Number'}]),
    ({'heading': "There are 3 different funding organisation IDs listed",
      'message': ("If you are expecting to be publishing data for multiple funders then "
                  "you can ignore this notice. If you are only publishing for a single funder then you should review "
                  "your <span class=\"highlight-background-text\">Funding Organisation identifier</span> "
                  "column to see where multiple IDs have occurred.")},
     ['grants/0/fundingOrganization/0/id', 'grants/1/fundingOrganization/0/id', 'grants/2/fundingOrganization/0/id'],
     [{'sheet': 'grants', 'letter': 'V', 'row_number': 2, 'header': 'Funding Org:Identifier'},
      {'sheet': 'grants', 'letter': 'V', 'row_number': 3, 'header': 'Funding Org:Identifier'},
      {'sheet': 'grants', 'letter': 'V', 'row_number': 4, 'header': 'Funding Org:Identifier'}])
]

USEFULNESS_CHECKS_RESULTS = [
    ({'heading': ("33% of grants have a <span class=\"highlight-background-text\">Recipient Org:Identifier</span> that "
                  "starts '360G-'"),
      'message': ("If the grant is to a recipient organisation that has an external "
                  "identifier (such as a charity or company number), then this should "
                  "be used instead. Using external identifiers helps people using your "
                  "data to match it up against other data - for example to see who else "
                  "has given grants to the same recipient, even if they’re known by a "
                  "different name. If no external identifier can be used, then you can "
                  "ignore this notice.")},
     ['grants/0/recipientOrganization/0/id'],
     [{'sheet': 'grants', 'letter': 'J', 'row_number': 2, 'header': 'Recipient Org:Identifier'}]),
    ({'heading': ("33% of grants have a <span class=\"highlight-background-text\">Funding Org:Identifier</span> that "
                  "starts '360G-'"),
      'message': ("If the grant is from a funding organisation that has an external identifier "
                  "(such as a charity or company number), then this should be used instead. "
                  "If no other identifier can be used, then you can ignore this notice.")},
     ['grants/1/fundingOrganization/0/id'],
     [{'sheet': 'grants', 'letter': 'V', 'row_number': 3, 'header': 'Funding Org:Identifier'}]),
    ({'heading': ("33% of grants do not have either a "
                  "<span class=\"highlight-background-text\">Recipient Org:Company Number</span> or a "
                  "<span class=\"highlight-background-text\">Recipient Org:Charity Number</span>"),
      'message': ("Providing one or both of these, if possible, makes it easier for users "
                  "to join up your data with other data sources to provide better insight "
                  "into grantmaking. If your grants are to organisations that don’t have UK "
                  "Company or UK Charity numbers, then you can ignore this notice.")},
     ['grants/2/recipientOrganization/0/id'],
     [{'sheet': 'grants', 'letter': 'J', 'row_number': 4, 'header': 'Recipient Org:Identifier'}]),
    ({'heading': "33% of grants do not have <span class=\"highlight-background-text\">Last Modified</span> information",
      'message': "<span class=\"highlight-background-text\">Last Modified</span> shows the date and time when "
                 "information about a grant was last updated in your file. Including this information allows data "
                 "users to see when changes have been made and reconcile differences between versions "
                 "of your data. Please note: this is the date when the data was modified in "
                 "your 360Giving file, rather than in any of your internal systems."},
     ['grants/1/id'],
     [{'sheet': 'grants', 'letter': 'A', 'row_number': 3, 'header': 'Identifier'}]),
    ({'heading': "67% of grants do not have <span class=\"highlight-background-text\">Data Source</span> information",
      'message': "<span class=\"highlight-background-text\">Data Source</span> informs users about where information "
                 "came from and is an important part of establishing trust in your data. This information should "
                 "be a web link pointing to the source of this data, which may be an original "
                 "360Giving data file, a file from which the data was converted, or your "
                 "organisation’s website."},
     ['grants/0/id', 'grants/2/id'],
     [{'sheet': 'grants', 'letter': 'A', 'row_number': 2, 'header': 'Identifier'},
      {'sheet': 'grants', 'letter': 'A', 'row_number': 4, 'header': 'Identifier'}])
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
    with open(os.path.join('cove_360', 'fixtures', 'fundingproviders-grants_malformed.json')) as fp:
        data.original_file.save('test.json', UploadedFile(fp))
    resp = client.get(data.get_absolute_url())
    assert resp.status_code == 200
    assert b'not well formed JSON' in resp.content


@pytest.mark.django_db
def test_explore_unconvertable_spreadsheet(client):
    data = SuppliedData.objects.create()
    with open(os.path.join('cove_360', 'fixtures', 'bad.xlsx'), 'rb') as fp:
        data.original_file.save('basic.xlsx', UploadedFile(fp))
    resp = client.get(data.get_absolute_url())
    assert resp.status_code == 200
    assert b'We think you tried to supply a spreadsheet, but we failed to convert it.' in resp.content


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
    assert run_extra_checks(GRANTS, SOURCE_MAP, TEST_CLASSES['additional']) == ADDITIONAL_CHECKS_RESULTS


def test_quality_accuracy_checks():
    assert run_extra_checks(GRANTS, SOURCE_MAP, TEST_CLASSES['quality_accuracy']) == QUALITY_ACCURACY_CHECKS_RESULTS


def test_usefulness_checks():
    assert run_extra_checks(GRANTS, SOURCE_MAP, TEST_CLASSES['usefulness']) == USEFULNESS_CHECKS_RESULTS


def test_extend_numbers():
    assert list(extend_numbers([2])) == [1, 2, 3]
    assert list(extend_numbers([4])) == [3, 4, 5]
    assert list(extend_numbers([4, 6])) == [3, 4, 5, 6, 7]
    assert list(extend_numbers([4, 7])) == [3, 4, 5, 6, 7, 8]
    assert list(extend_numbers([4, 8])) == [3, 4, 5, 7, 8, 9]
    assert list(extend_numbers([1])) == [1, 2]
    assert list(extend_numbers([4, 5, 6])) == [3, 4, 5, 6, 7]
    assert list(extend_numbers([4, 5, 7, 2001])) == [3, 4, 5, 6, 7, 8, 2000, 2001, 2002]
