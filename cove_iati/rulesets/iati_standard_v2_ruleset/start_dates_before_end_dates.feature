Feature: Start dates chronologically before end dates

  Scenario Outline: result-indicator-period: start @iso-date date must be before end @iso-date
    Given `result/indicator/period/period-start` plus `result/indicator/period/period-end`
      Then both `iso-date` attributes must be a valid date
        And `iso-date` start date attribute must be chronologically before end date attribute

  Scenario Outline: recipient-organisation-budget-period: start @iso-date date must be before end @iso-date
    Given `recipient-org-budget/period-start` plus `recipient-org-budget/period-end`
      Then both `iso-date` attributes must be a valid date
        And `iso-date` start date attribute must be chronologically before end date attribute

  Scenario Outline: recipient-region-budget-period: start @iso-date date must be before end @iso-date
    Given `recipient-region-budget/period-start` plus `recipient-region-budget/period-end`
      Then both `iso-date` attributes must be a valid date
        And `iso-date` start date attribute must be chronologically before end date attribute

  Scenario Outline: planned-disbursement-period: start @iso-date date must be before end @iso-date
    Given `planned-disbursement/period-start` plus `planned-disbursement/period-end`
      Then both `iso-date` attributes must be a valid date
        And `iso-date` start date attribute must be chronologically before end date attribute

  Scenario Outline: recipient-country-budget-period: start @iso-date date must be before end:@iso-date
    Given `recipient-country-budget/period-start` plus `recipient-country-budget/period-end`
      Then both `iso-date` attributes must be a valid date
        And `iso-date` start date attribute must be chronologically before end date attribute

  Scenario Outline: total-expenditure-period: start @iso-date date must be before end @iso-date
    Given `total-expenditure/period-start` plus `total-expenditure/period-end`
      Then both `iso-date` attributes must be a valid date
        And `iso-date` start date attribute must be chronologically before end date attribute

  Scenario Outline: activity-date[@type="1"]: start @iso-date date must be before end @iso-date
    Given `activity-date[@type="1"]` plus `activity-date[@type="3"]`
      Then both `iso-date` attributes must be a valid date
        And `iso-date` start date attribute must be chronologically before end date attribute

  Scenario Outline: activity-date[@type="2"]: start @iso-date date must be before end @iso-date
    Given `activity-date[@type="2"]` plus `activity-date[@type="4"]`
      Then both `iso-date` attributes must be a valid date
        And `iso-date` start date attribute must be chronologically before end date attribute

  Scenario Outline: budget-period: start @iso-date date must be before end @iso-date
    Given `budget/period-start` plus `budget/period-end`
      Then both `iso-date` attributes must be a valid date
        And `iso-date` start date attribute must be chronologically before end date attribute

  Scenario Outline: total-budget-period: start @iso-date date must be before end @iso-date
    Given `total-budget/period-start` plus `total-budget/period-start`
      Then both `iso-date` attributes must be a valid date
        And `iso-date` start date attribute must be chronologically before end date attribute
