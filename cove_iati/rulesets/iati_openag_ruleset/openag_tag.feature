Feature: openag:tag element is expected and must contain specific attributes

  Scenario Outline: openag-tag: element is expected
    Given an Open Agriculture IATI activity
     Then at least one `openag:tag` element is expected

  Scenario Outline: openag-tag: element must have @vocabulary attribute with code for "maintained by the Reporting Organisation"
    Given `openag:tag` elements
     Then every `openag:tag` must have `vocabulary` attribute
       And every `vocabulary` must be equal to `98 or 99`

  Scenario Outline: openag-tag: element must have @vocabulary-uri attribute with Agrovoc URI
    Given `openag:tag` elements
     Then every `openag:tag` must have `vocabulary-uri` attribute
       And every `vocabulary-uri` must be equal to `http://aims.fao.org/aos/agrovoc/`

  Scenario Outline: openag-tag: element must have @code attribute
    Given `openag:tag` elements
     Then every `openag:tag` must have `code` attribute
