Feature: Sector

  Scenario Outline: Sector is present
    Given an IATI activity
     then either `sector` or `transaction/sector` should be present

  Scenario Outline: If sector is present, transaction/sector should not be
    Given `sector` is present
     then `transaction/sector` should not be present

  Scenario Outline: If transaction/sector is present, sector should not be
    Given `transaction/sector` is present
     then `sector` should not be present
