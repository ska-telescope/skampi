@VTS-226
Feature: Dish simulator confidence test via TM-Dish interface
	# The Dish Simulator behaviour is tested by invoking the commands of the Dish master TANGO
	# device and verifying that dishMode transitions are as per the documentation.

	#Scenario: Dish from dish_mode_a to dish_mode_b
	@XTP-813 @XTP-811
	Scenario Outline: when the telescope subarrays can be aborted then abort brings them in ABORTED
		Given operator John has a running telescope with a subarray in state <subarray_obsstate>
		When operator issues the ABORT command
		Then the subarray eventually goes into ABORTED
		
		Examples:
		| subarray_obsstate  | 
		| IDLE               | 
		| READY              | 
		| SCANNING           | 


