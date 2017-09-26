Feature: openag:tag element checks

  Scenario Outline: openag-tag: element is expected
    Given an Open Agriculture IATI activity
     then at least one `openag:tag` is expected

  Scenario Outline: openag-tag: element must use vocabulary maintained by the Reporting Organisation
    Given openag:tag elements
     then every `openag:tag` must have @vocabulary="98"|"99"

  Scenario Outline: openag-tag: element must use Agrovoc vocabulary-uri
    Given openag:tag elements
     then every `openag:tag` must have @vocabulary-uri=="http://aims.fao.org/aos/agrovoc/"

  Scenario Outline: openag-tag: element must use code attribute
    Given openag:tag elements
     then every `openag:tag` must have @code
