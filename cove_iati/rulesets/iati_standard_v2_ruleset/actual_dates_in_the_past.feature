Feature: Actual dates must be in the past

  Scenario Outline: activity-date[@type='2'].@iso-date must be today or in the past
    Given `.` elements
      Then `activity-date[@type='2']/@iso-date` must be today or in the past

  Scenario Outline: activity-date[@type='4'].@iso-date must be today or in the past
    Given `.` elements
      Then `activity-date[@type='4']/@iso-date` must be today or in the past

  Scenario Outline: transaction.transaction-date.@iso-date date must be today or in the past
    Given `transaction` elements
      Then `transaction-date/@iso-date` must be today or in the past

  Scenario Outline: transaction.value.@value-date must be today or in the past
    Given `transaction` elements
      Then `value/@value-date` must be today or in the past
