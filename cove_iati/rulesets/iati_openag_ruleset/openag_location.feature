Feature: location element must be present and must contain location-id with attributes

  Scenario Outline: location: element is expected
    Given an Open Agriculture IATI activity
     Then at least one `location` element is expected

  Scenario Outline: location: element must include <location-id>
    Given `location` elements
     Then every `location` must include `location-id` element

  Scenario Outline: location: element must use @code attribute
    Given `location/location-id` elements
     Then every `location/location-id` must have `code` attribute

  Scenario Outline: location: element must use @vocabulary attribute
    Given `location/location-id` elements
     Then every `location/location-id` must have `vocabulary` attribute
