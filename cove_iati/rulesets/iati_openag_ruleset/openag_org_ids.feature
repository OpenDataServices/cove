Feature: organisation identifiers must use org-id prefixes 

  Scenario Outline: reporting-org: @ref should have an org-id prefix
    Given `reporting-org/@ref` identifier attribute
     then `reporting-org/@ref` should start with an org-id prefix

  Scenario Outline: transaction-provider-organisation: @ref should have an org-id prefix
    Given `transaction/provider-org/@ref` identifier attribute
     then `transaction/provider-org/@ref` should start with an org-id prefix

  Scenario Outline: transaction-receiver-organisation: @ref should have an org-id prefix
    Given `other-identifier/owner-org/@ref` identifier attribute
     then `other-identifier/owner-org/@ref` should start with an org-id prefix

  Scenario Outline: transaction-receiver-organisation: @ref should have an org-id prefix
    Given `transaction/receiver-org/@ref` identifier attribute
     then `transaction/receiver-org/@ref` should start with an org-id prefix

  Scenario Outline: participating-org: @ref should have an org-id prefix
    Given `participating-org/@ref` identifier attribute
     then every `participating-org/@ref` should start with an org-id prefix
