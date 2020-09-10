@VTS-228
Feature: Transaction ID logging
	#The start and end of every transaction should be logged with an ID.
	# If starting a new transaction, then a new ID must be generated.
	# This ID should be accessible for reuse for downstream transactions.

	
	@XTP-1080 @XTP-1079 @PI8
	Scenario Outline: Executing a new transaction
		Given an example transaction logging application
		And a transaction ID is not present
		When executing a transaction named <command_name>
		Then a new transaction ID is generated
		And start of transaction is logged including that transaction ID and name <command_name>
		And end of transaction is logged including that transaction ID and name <command_name>
		
		Examples:
		| command_name |
		| Configure    |