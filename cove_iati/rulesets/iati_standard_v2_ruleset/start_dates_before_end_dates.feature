Feature: Start dates chronologically before end dates

  Scenario Outline: result:indicator:period-start:@iso-date date must be before period-end:@iso-date
    Given `result/indicator/period/period-start/@iso-date` is a valid date
     and `result/indicator/period/period-end/@iso-date` is a valid date
     then `result/indicator/period/period-start/@iso-date` should be chronologically before `result/indicator/period/period-end/@iso-date`

  Scenario Outline: recipient-organisation-budget:period-start/@iso-date date must be before period-end:@iso-date
    Given `recipient-org-budget/period-start/@iso-date` is a valid date
     and `recipient-org-budget/period-end/@iso-date` is a valid date
     then `recipient-org-budget/period-start/@iso-date` should be chronologically before `recipient-org-budget/period-end/@iso-date`

  Scenario Outline: recipient-region-budget:period-start:@iso-date date must be before recipient-region-budget:period-end:@iso-date
    Given `recipient-region-budget/period-start/@iso-date` is a valid date
     and `recipient-region-budget/period-end/@iso-date` is a valid date
     then `recipient-region-budget/period-start/@iso-date` should be chronologically before `recipient-region-budget/period-end/@iso-date`

  Scenario Outline: planned-disbursement:period-start:@iso-date date must be before planned-disbursement:period-end:@iso-date
    Given `planned-disbursement/period-start/@iso-date` is a valid date
     and `planned-disbursement/period-end/@iso-date` is a valid date
     then `planned-disbursement/period-start/@iso-date` should be chronologically before `planned-disbursement/period-end/@iso-date`

  Scenario Outline: recipient-country-budget:period-start:@iso-date date must be before recipient-country-budget:period-end:@iso-date
    Given `recipient-country-budget/period-start/@iso-date` is a valid date
     and `recipient-country-budget/period-end/@iso-date` is a valid date
     then `recipient-country-budget/period-start/@iso-date` should be chronologically before `recipient-country-budget/period-end/@iso-date`

  Scenario Outline: total-expenditure:period-start:@iso-date date must be before total-expenditure:period-end:@iso-date
    Given `total-expenditure/period-start/@iso-date` is a valid date
     and `total-expenditure/period-end/@iso-date` is a valid date
     then `total-expenditure/period-start/@iso-date` should be chronologically before `total-expenditure/period-end/@iso-date`

  Scenario Outline: activity-date[@type="start-planned"]:@iso-date date must be before activity-date[@type="end-planned"]:@iso-date (IATI 1.x)
    Given `activity-date[@type="start-planned"]/@iso-date` is a valid date
     and `activity-date[@type="end-planned"]/@iso-date` is a valid date
     then `activity-date[@type="start-planned"]/@iso-date` should be chronologically before `activity-date[@type="end-planned"]/@iso-date`

  Scenario Outline: activity-date[@type="1"]:@iso-date date must be before activity-date[@type="3"]:@iso-date
    Given `activity-date[@type="1"]/@iso-date` is a valid date
     and `activity-date[@type="3"]/@iso-date` is a valid date
     then `activity-date[@type="1"]/@iso-date` should be chronologically before `activity-date[@type="3"]/@iso-date`


  Scenario Outline: activity-date[@type="2"]:@iso-date date must be before activity-date[@type="4"]:@iso-date
    Given `activity-date[@type="2"]/@iso-date` is a valid date
     and `activity-date[@type="4"]/@iso-date` is a valid date
     then `activity-date[@type="2"]/@iso-date` should be chronologically before `activity-date[@type="4"]/@iso-date`

  Scenario Outline: budget:period-start:@iso-date date must be before budget:period-end:@iso-date
    Given `budget/period-start/@iso-date` is a valid date
     and `budget/period-end/@iso-date` is a valid date
     then `budget/period-start/@iso-date` should be chronologically before `budget/period-end/@iso-date`

  Scenario Outline: total-budget:period-start:@iso-date date must be before total-budget:period-end:@iso-date
    Given `total-budget/period-start/@iso-date` is a valid date
     and `total-budget/period-end/@iso-date` is a valid date
     then `total-budget/period-start/@iso-date` should be chronologically before `total-budget/period-end/@iso-date`
