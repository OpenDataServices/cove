Feature: Mandatory elements

  Scenario Outline: activity-date[date @type="1"] or activity-date[@type="2"] must be present
    Given an IATI activity
    Then either `activity-date[@type="1"]` or `activity-date[@type="2"]` is expected

  Scenario Outline: participating-org.@ref attribute or participating-org.narrative must be present
    Given `participating-org` organisations
    Then either `participating-org/@ref` or `participating-org/narrative/text()` is expected
