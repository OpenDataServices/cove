Feature: tag element is expected and must contain specific attributes

  Scenario Outline: tag element must be present
    Given an IATI activity
     Then at least one `tag` element is expected

  Scenario Outline: tag.@vocabulary must be present with a code for "maintained by the Reporting Organisation"
    Given `tag` elements
     Then must have `vocabulary` attribute
       And every `vocabulary` must be equal to `1 or 98 or 99`

  Scenario Outline: tag.@vocabulary-uri must be present with an Agrovoc URI
    Given `tag[@vocabulary="98" or @vocabulary="99"]` elements
     Then must have `vocabulary-uri` attribute
       And every `vocabulary-uri` must be equal to `http://aims.fao.org/aos/agrovoc/`

  Scenario Outline: tag.@code must be present
    Given `tag` elements
     Then must have `code` attribute
