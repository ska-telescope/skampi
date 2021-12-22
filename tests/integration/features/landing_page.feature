@XTP-3898
Feature: Landing Page Availability and link generation

	
	@XTP-3899 @XTP-3901 @XTP-3348
	Scenario: Test landing page available on ska mid
		Given a deployed ska-mid
		When I access the landing page url in the browser
		Then the landing page is rendered correctly	

	
	@XTP-3900 @XTP-3901 @XTP-3348
	Scenario: Test Landing Page Navigability on ska mid
		Given a deployed ska-mid
		Given a landing page available to a web browser
		When I access the landing page url in the browser
		Then I expect to be able to navigate to the <given link>

		Examples:
		|given link|
		|taranta root|
		|kibana logging|
		|eda|
		|about:versioning|


	
	@XTP-3903 @XTP-3901 @XTP-3348
	Scenario Outline: Test Landing Page Navigability on ska low
		Given a deployed ska-mid
		Given a landing page available to a web browser
		When I access the landing page url in the browser
		Then I expect to be able to navigate to the <given link>	

	
	@XTP-3902 @XTP-3901 @XTP-3348
	Scenario: Test landing page available on ska low
		Given a deployed ska-low
		When I access the landing page url in the browser
		Then the landing page is rendered correctly