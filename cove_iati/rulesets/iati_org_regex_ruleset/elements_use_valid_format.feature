Feature: Elements must use a valid format

  Scenario Outline: reporting-org.@ref should match the regex [^\:\&\|\?]+
    Given `reporting-org` organisations
     Then `ref` attribute should match the regex `^[^\/\&\|\?]+$`

  Scenario Outline: participating-org.@ref should match the regex [^\:\&\|\?]+
    Given `participating-org` organisations
     Then `ref` attribute should match the regex `^[^\/\&\|\?]+$`

  Scenario Outline: transaction.provider-organisation.@ref should match the regex [^\:\&\|\?]+
    Given `transaction/provider-org` organisations
     Then `ref` attribute should match the regex `^[^\/\&\|\?]+$`

  Scenario Outline: transaction.receiver-organisation.@ref should match the regex [^\:\&\|\?]+
    Given `transaction/receiver-org` organisations
     Then `ref` attribute should match the regex `^[^\/\&\|\?]+$`
