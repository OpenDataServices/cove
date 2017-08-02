Feature: Elements use a valid format

  Scenario Outline: iati-identifier should match the regex [^\:\&\|\?]+
    Given `iati-identifier/text()` is present
     then every `iati-identifier/text()` should match the regex `^[^\/\&\|\?]+$`

  Scenario Outline: reporting-org @ref should match the regex [^\:\&\|\?]+
    Given `reporting-org/@ref` is present
     then every `reporting-org/@ref` should match the regex `^[^\/\&\|\?]+$`

  Scenario Outline: participating-org @ref should match the regex [^\:\&\|\?]+
    Given `participating-org/@ref` is present
     then every `participating-org/@ref` should match the regex `^[^\/\&\|\?]+$`

  Scenario Outline: transaction:provider-organisation @ref should match the regex [^\:\&\|\?]+
    Given `transaction/provider-org/@ref` is present
     then every `transaction/provider-org/@ref` should match the regex `^[^\/\&\|\?]+$`

  Scenario Outline: transaction:receiver-organisation @ref should match the regex [^\:\&\|\?]+
    Given `transaction/receiver-org/@ref` is present
     then every `transaction/receiver-org/@ref` should match the regex `^[^\/\&\|\?]+$`
