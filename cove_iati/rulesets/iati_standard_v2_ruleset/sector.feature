Feature: Sector

  Scenario Outline: sector sector or transaction:sector must be present
    Given an IATI activity
     then either `sector` or `transaction/sector` should be present

  Scenario Outline: sector either sector or transaction:sector must be present but not both
    Given `sector` is present
     then `transaction/sector` should not be present
