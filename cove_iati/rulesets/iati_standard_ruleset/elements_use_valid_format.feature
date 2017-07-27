Feature: Elements use a valid format

  Scenario Outline: IATI identifier (regex)
    Given `iati-identifier/text()` is present
     then every `iati-identifier/text()` should match the regex `^[^\/\&\|\?]+$`

  Scenario Outline: Reporting organisation reference (regex)
    Given `reporting-org/@ref` is present
     then every `reporting-org/@ref` should match the regex `^[^\/\&\|\?]+$`

  Scenario Outline: Participating organisation reference (regex)
    Given `participating-org/@ref` is present
     then every `participating-org/@ref` should match the regex `^[^\/\&\|\?]+$`

  Scenario Outline: Provider organisation reference (regex)
    Given `transaction/provider-org/@ref` is present
     then every `transaction/provider-org/@ref` should match the regex `^[^\/\&\|\?]+$`

  Scenario Outline: Receiver organisation reference (regex)
    Given `transaction/receiver-org/@ref` is present
     then every `transaction/receiver-org/@ref` should match the regex `^[^\/\&\|\?]+$`
