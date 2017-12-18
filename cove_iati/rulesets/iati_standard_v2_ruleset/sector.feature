Feature: Sector must be specified

  Scenario Outline: either sector or transaction.sector must be present
    Given an IATI activity
     Then either `sector` or `transaction/sector` is expected, but not both
