Feature: Location element must be present and must contain location-id with attributes

  Scenario Outline: location element must be present
    Given an IATI activity
     Then at least one `location` element is expected

  Scenario Outline: location.location-id must be present
    Given `location` elements
     Then every `location` must include `location-id` element

  Scenario Outline: location.@code must be present
    Given `location/location-id` elements
     Then every `location/location-id` must have `code` attribute

  Scenario Outline: location.@vocabulary must be present
    Given `location/location-id` elements
     Then every `location/location-id` must have `vocabulary` attribute
