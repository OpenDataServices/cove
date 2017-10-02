Feature: Mandatory elements

  Scenario Outline: activity-date: date @type="1" or date @type="2" is expected
    Given an IATI activity
     then either `activity-date[@type="1"]` or `activity-date[@type="2"]` is expected

  Scenario Outline: participating-org: @ref attribute or narrative is expected
    Given `participating-org` organisations
     then either `participating-org/@ref` or `participating-org/narrative/text()` is expected
