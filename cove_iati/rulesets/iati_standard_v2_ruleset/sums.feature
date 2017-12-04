Feature: Percentages must sum to 100

  Scenario Outline: recipient-country.@percentage and recipient-region.@percentage must sum to 100
    Given `recipient-country|recipient-region` elements
      Then `percentage` attribute must sum to 100
