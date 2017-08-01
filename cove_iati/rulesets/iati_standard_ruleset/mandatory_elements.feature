Feature: Mandatory elements

  Scenario Outline: activity-date @type="start-planned" or @type="start-actual" must be present (IATI 1.x)
    Given an IATI activity
     then either `activity-date[@type="start-planned"]` or `activity-date[@type="start-actual"]` should be present

  Scenario Outline: activity-date @type="1" or @type="2" must be present (IATI 2.x)
    Given an IATI activity
     then either `activity-date[@type="1"] or `activity-date[@type="2"] should be present

  Scenario Outline: participating-org either @ref or narrative must be present
    Given `participating-org` is present
     then either `participating-org/@ref` or `participating-org/narrative/text()` should be present
