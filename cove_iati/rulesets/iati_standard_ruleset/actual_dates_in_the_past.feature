Feature: Actual dates should be in the past

  Scenario Outline: Actual start dates past (IATI 1.x)
    Given `activity-date[@type='start-actual']/@iso-date` is a valid date
     then `activity-date[@type='start-actual']/@iso-date` should be today, or in the past

  Scenario Outline: Actual start dates past (IATI 2.x)
    Given `activity-date[@type='2']/@iso-date` is a valid date
     then `activity-date[@type='2']/@iso-date` should be today, or in the past

  Scenario Outline: Actual end dates past (IATI 1.x)
    Given `activity-date[@type='end-actual']/@iso-date` is a valid date
     then `activity-date[@type='end-actual']/@iso-date` should be today, or in the past

  Scenario Outline: Actual end dates past (IATI 2.x)
    Given `activity-date[@type='4']/@iso-date` is a valid date
     then `activity-date[@type='4']/@iso-date` should be today, or in the past

  Scenario Outline: Transaction dates past
    Given `transaction/transaction-date/@iso-date` is a valid date
     then `transaction/transaction-date/@iso-date` should be today, or in the past

  Scenario Outline: Value dates past
    Given `transaction/value-date/@iso-date` is a valid date
     then `transaction/value-date/@iso-date` should be today, or in the past
