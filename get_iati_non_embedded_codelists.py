import os
import requests

non_embedded_codelist_files = [
    "ActivityScope.xml",
    "AidType-category.xml",
    "AidTypeVocabulary.xml",
    "AidType.xml",
    "BudgetIdentifierSector-category.xml",
    "BudgetIdentifierSector.xml",
    "BudgetIdentifierVocabulary.xml",
    "BudgetIdentifier.xml",
    "BudgetNotProvided.xml",
    "CollaborationType.xml",
    "ConditionType.xml",
    "ContactType.xml",
    "Country.xml",
    "CRSAddOtherFlags.xml",
    "CRSChannelCode.xml",
    "Currency.xml",
    "DescriptionType.xml",
    "DisbursementChannel.xml",
    "DocumentCategory-category.xml",
    "EarmarkingCategory.xml",
    "FileFormat.xml",
    "FinanceType-category.xml",
    "FinanceType.xml",
    "FlowType.xml",
    "GeographicalPrecision.xml",
    "GeographicExactness.xml",
    "GeographicLocationClass.xml",
    "GeographicLocationReach.xml",
    "GeographicVocabulary.xml",
    "HumanitarianScopeType.xml",
    "HumanitarianScopeVocabulary.xml",
    "IATIOrganisationIdentifier.xml",
    "IndicatorMeasure.xml",
    "IndicatorVocabulary.xml",
    "Language.xml",
    "LoanRepaymentPeriod.xml",
    "LoanRepaymentType.xml",
    "LocationType-category.xml",
    "LocationType.xml",
    "OrganisationIdentifier.xml",
    "OrganisationRegistrationAgency.xml",
    "OrganisationType.xml",
    "OtherIdentifierType.xml",
    "PolicyMarkerVocabulary.xml",
    "PolicyMarker.xml",
    "PolicySignificance.xml",
    "PublisherType.xml",
    "RegionVocabulary.xml",
    "Region.xml",
    "ResultType.xml",
    "ResultVocabulary.xml",
    "SectorCategory.xml",
    "SectorVocabulary.xml",
    "Sector.xml",
    "TagVocabulary.xml",
    "TiedStatus.xml",
    "VerificationStatus.xml",
    "Version.xml"
]

dir_path = os.path.dirname(os.path.realpath(__file__))


def get_iati_non_embeded_codelists():
    url = 'https://raw.githubusercontent.com/IATI/IATI-Codelists-NonEmbedded/master/xml/'

    for filename in non_embedded_codelist_files:
        with open(os.path.join(dir_path, 'cove_iati', 'non_embedded_codelists', filename), 'wb+') as fp:
            fp.write(requests.get(url + filename).content)


if __name__ == "__main__":
    get_iati_non_embeded_codelists()
