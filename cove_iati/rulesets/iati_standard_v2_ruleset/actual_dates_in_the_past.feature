Feature: Actual dates should be in the past

  Scenario Outline: activity-date[@type='2']:@iso-date date must be today or in the past
    Given `activity-date[@type='2']/@iso-date` is a valid date
     then `activity-date[@type='2']/@iso-date` should be today, or in the past

  Scenario Outline: activity-date[@type='4']:@iso-date date must be today or in the past
    Given `activity-date[@type='4']/@iso-date` is a valid date
     then `activity-date[@type='4']/@iso-date` should be today, or in the past

  Scenario Outline: transaction:transaction-date:@iso-date date must be today or in the past
    Given `transaction/transaction-date/@iso-date` is a valid date
      then `transaction/transaction-date/@iso-date` should be today, or in the past

  Scenario Outline: transaction:value:@value-date date must be today or in the past
    Given `transaction/value/@value-date` is a valid date
      then `transaction/value/@value-date` should be today, or in the past
