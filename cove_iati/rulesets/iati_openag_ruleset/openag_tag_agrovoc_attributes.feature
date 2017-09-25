Feature: openag:tag element checks

  Scenario Outline: openag-tag: element is expected
    Given an Open Agriculture IATI activity
     then at least one `openag:tag` is expected

  Scenario Outline: openag-tag: must use Agrovoc
    Given openag:tag elements
     then at least one `openag:tag` must use Agrovoc classification
