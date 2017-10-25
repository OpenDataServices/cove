Feature: Start dates chronologically before end dates

  Scenario Outline: result-indicator.period-start.@iso-date must be before result-indicator.period-end.@iso-date
    Given `result/indicator/period` elements
      Then `period-start/@iso-date` must be chronologically before `period-end/@iso-date`

  Scenario Outline: recipient-organisation-budget.period-start.@iso-date must be before recipient-organisation-budget.period-end.@iso-date
    Given `recipient-org-budget` elements
      Then `period-start/@iso-date` must be chronologically before `period-end/@iso-date`

  Scenario Outline: recipient-region-budget.period-start.@iso-date must be before recipient-region-budget.period-end.@iso-date
    Given `recipient-region-budget` elements
      Then `period-start/@iso-date` must be chronologically before `period-end/@iso-date`

  Scenario Outline: planned-disbursement.period-start.@iso-date must be before planned-disbursement.period-end.@iso-date
    Given `planned-disbursement` elements
      Then `period-start/@iso-date` must be chronologically before `period-end/@iso-date`

  Scenario Outline: recipient-country-budget.period-start.@iso-date must be before recipient-country-budget.period-end.@iso-date
    Given `recipient-country-budget` elements
      Then `period-start/@iso-date` must be chronologically before `period-end/@iso-date`

  Scenario Outline: total-expenditure.period-start.@iso-date must be before total-expenditure.period-end.@iso-date
    Given `total-expenditure` elements
      Then `period-start/@iso-date` must be chronologically before `period-end/@iso-date`

  Scenario Outline: activity-date[@type="1"].@iso-date must be before activity-date[@type="3"].@iso-date
    Given `.` elements
      Then `activity-date[@type="1"]/@iso-date` must be chronologically before `activity-date[@type="3"]/@iso-date`

  Scenario Outline: activity-date[@type="2"].@iso-date must be before activity-date[@type="4"].@iso-date
    Given `.` elements
      Then `activity-date[@type="2"]/@iso-date` must be chronologically before `activity-date[@type="4"]/@iso-date`

  Scenario Outline: budget-period.period-start.@iso-date must be before budget-period.period-end.@iso-date
    Given `budget` elements
      Then `period-start/@iso-date` must be chronologically before `period-end/@iso-date`

  Scenario Outline: total-budget.period-start.@iso-date must be before total-budget.period-end.@iso-date
    Given `total-budget` elements
      Then `period-start/@iso-date` must be chronologically before `period-end/@iso-date`
