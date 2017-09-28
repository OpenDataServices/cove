Feature: organisation identifiers must use org-ids prefixes 

  Scenario Outline: reporting-org: @ref should have an org-ids prefix
    Given `reporting-org` organisation
     then `ref` id attribute should start with an org-ids prefix

  Scenario Outline: transaction-provider-organisation: @ref should have an org-ids prefix
    Given `transaction/provider-org` organisation
     then `ref` id attribute should start with an org-ids prefix

  Scenario Outline: transaction-receiver-organisation: @ref should have an org-ids prefix
    Given `other-identifier/owner-org` organisation
     then `ref` id attribute should start with an org-ids prefix

  Scenario Outline: transaction-receiver-organisation: @ref should have an org-ids prefix
    Given `transaction/receiver-org` organisation
     then `ref` id attribute should start with an org-ids prefix

  Scenario Outline: participating-org: @ref should have an org-ids prefix
    Given `participating-org` organisation
     then `ref` id attribute should start with an org-ids prefix
