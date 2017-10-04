Feature: Sector

  Scenario Outline: sector or transaction sector must be present (but not both)
    Given an IATI activity
     Then either `sector` or `transaction/sector` is expected
