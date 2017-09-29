Feature: Sector

  Scenario Outline: sector sector or transaction:sector are expected
    Given an IATI activity
     Then either `sector` or `transaction/sector` is expected

  Scenario Outline: sector either sector or transaction:sector are expected but not both
    Given `sector` elements
     then `transaction/sector` is not expected
