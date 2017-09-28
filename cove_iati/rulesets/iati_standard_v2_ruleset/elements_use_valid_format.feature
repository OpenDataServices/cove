Feature: Elements use a valid format

  Scenario Outline: text identifier should match the regex [^\:\&\|\?]+
    Given `iati-identifier/text()` texts
     then every `iati-identifier/text()` should match the regex `^[^\/\&\|\?]+$`

  Scenario Outline: reporting-org:@ref @ref should match the regex [^\:\&\|\?]+
    Given `reporting-org/@ref` organisations
     then every `reporting-org/@ref` should match the regex `^[^\/\&\|\?]+$`

  Scenario Outline: participating-org:@ref @ref should match the regex [^\:\&\|\?]+
    Given `participating-org/@ref` organisations
     then every `participating-org/@ref` should match the regex `^[^\/\&\|\?]+$`

  Scenario Outline: transaction:provider-organisation:@ref @ref should match the regex [^\:\&\|\?]+
    Given `transaction/provider-org/@ref` organisations
     then every `transaction/provider-org/@ref` should match the regex `^[^\/\&\|\?]+$`

  Scenario Outline: transaction:receiver-organisation:@ref @ref should match the regex [^\:\&\|\?]+
    Given `transaction/receiver-org/@ref` organisations
     then every `transaction/receiver-org/@ref` should match the regex `^[^\/\&\|\?]+$`
