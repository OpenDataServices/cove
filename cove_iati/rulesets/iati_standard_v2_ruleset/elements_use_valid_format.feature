Feature: Elements must use a valid format

  Scenario Outline: identifier.text() should match the regex [^\:\&\|\?]+
    Given `iati-identifier` elements
     Then iati-identifier text should match the regex `^[^\/\&\|\?]+$`
