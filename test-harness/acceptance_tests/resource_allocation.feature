Feature: Resource allocation 
        Feature to allocate resources to a subarray.

Scenario: Allocate Resources
        Given The telescope is ready
        Given A subarray definition
        Given A resource allocation definition
        Given a means of observing the tmc subarray
        Given a means of observing the csp subarray
        Given a means of observing the csp master
        Given a means of observing the sdp subarray
        Given there are not previously allocated resources
        Given a monitor on tmc subarray state
        Given a way of monitoring receptor ID list
        Given a way to report on the subarray status
        When I allocate resources to a subarray
        Then the subarray is correctly allocated
