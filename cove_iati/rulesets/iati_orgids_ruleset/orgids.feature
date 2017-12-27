Feature: Organisation identifiers must use org-ids prefixes

  Scenario Outline: reporting-org.@ref must have an org-ids prefix
    Given `reporting-org` organisations
     Then `ref` id attribute must start with an org-ids prefix

  Scenario Outline: transaction.provider-org.@ref must have an org-ids prefix
    Given `transaction/provider-org` organisations
     Then `ref` id attribute must start with an org-ids prefix

  Scenario Outline: other-identifier.owner-org.@ref must have an org-ids prefix
    Given `other-identifier/owner-org` organisations
     Then `ref` id attribute must start with an org-ids prefix

  Scenario Outline: transaction.receiver-org.@ref must have an org-ids prefix
    Given `transaction/receiver-org` organisations
     Then `ref` id attribute must start with an org-ids prefix

  Scenario Outline: participating-org.@ref must have an org-ids prefix
    Given `participating-org` organisations
     Then `ref` id attribute must start with an org-ids prefix
