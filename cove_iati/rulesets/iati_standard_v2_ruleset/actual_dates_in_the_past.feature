Feature: Actual dates must be in the past

  Scenario Outline: activity-date[@type='2']:@iso-date date must be today or in the past
    Given `activity-date[@type='2']` elements
      Then `iso-date` attribute must be a valid date
        And `iso-date` must be today, or in the past

  Scenario Outline: activity-date[@type='4']:@iso-date date must today or in the past
    Given `activity-date[@type='4']` elements
      Then `iso-date` attribute must be a valid date
        And `iso-date` attribute must be today or in the past

  Scenario Outline: transaction:transaction-date:@iso-date date must be today or in the past
    Given `transaction/transaction-date` elements
      Then `iso-date` attribute must be a valid date
        And `iso-date` attribute must be today or in the past

  Scenario Outline: transaction:value:@value-date date must be today or in the past
    Given `transaction/value` elements
      Then `value-date` attribute must be a valid date
        And `value-date` attribute must be today or in the past
