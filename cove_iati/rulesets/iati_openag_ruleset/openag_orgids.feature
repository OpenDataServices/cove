Feature: organisation identifiers must use org-id prefixes 

  Scenario Outline: reporting-org: @ref should have an org-id prefix
    Given `reporting-org` organisation
     then `ref` attribute should start with an org-id prefix

  Scenario Outline: transaction-provider-organisation: @ref should have an org-id prefix
    Given `transaction/provider-org/` organisation
     then `ref` attribute should start with an org-id prefix

  Scenario Outline: transaction-receiver-organisation: @ref should have an org-id prefix
    Given `other-identifier/owner-org/` organisation
     then `ref` attribute should start with an org-id prefix

  Scenario Outline: transaction-receiver-organisation: @ref should have an org-id prefix
    Given `transaction/receiver-org/` organisation
     then `ref` attribute should start with an org-id prefix

  Scenario Outline: participating-org: @ref should have an org-id prefix
    Given `participating-org` organisations
     then every `ref` attribute should start with an org-id prefix
