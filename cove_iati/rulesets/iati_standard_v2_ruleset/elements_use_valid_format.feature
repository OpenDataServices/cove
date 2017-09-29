Feature: Elements use a valid format

  Scenario Outline: text identifier should match the regex [^\:\&\|\?]+
    Given `iati-identifier` elements
     then iati-identifier text should match the regex `^[^\/\&\|\?]+$`

  Scenario Outline: reporting-org:@ref @ref should match the regex [^\:\&\|\?]+
    Given `reporting-org` organisations
     then `ref` attribute should match the regex `^[^\/\&\|\?]+$`

  Scenario Outline: participating-org:@ref @ref should match the regex [^\:\&\|\?]+
    Given `participating-org` organisations
     then `ref` attribute should match the regex `^[^\/\&\|\?]+$`

  Scenario Outline: transaction:provider-organisation:@ref @ref should match the regex [^\:\&\|\?]+
    Given `transaction/provider-org` organisations
     then `ref` attribute should match the regex `^[^\/\&\|\?]+$`

  Scenario Outline: transaction:receiver-organisation:@ref @ref should match the regex [^\:\&\|\?]+
    Given `transaction/receiver-org` organisations
     then `ref` attribute should match the regex `^[^\/\&\|\?]+$`
