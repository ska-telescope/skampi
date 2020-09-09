@VTS-228
Feature: Transaction ID logging
	# The start and end of every transaction should be logged with an ID.
	# If starting a new transaction, then a new ID must be generated.
	# This ID should be accessible for reuse for downstream transactions.

	
	@XTP-1080 @XTP-1079 @PI8
	Scenario: Executing a new transaction
		Given an example transaction logging application
		When executing a transaction
		And no transaction ID is present
		Then a new transaction ID is generated
		And start of transaction is logged including transaction ID and name
		And end of transaction is logged including transaction ID and name	

	
	@XTP-1081 @XTP-1079 @PI8
	Scenario: Continuing an existing transaction
		Given an example transaction logging application
		When executing a transaction
		And the transaction ID is 12345
		Then the transaction ID used is 12345
		And start of transaction is logged including transaction ID and name
		And end of transaction is logged including transaction ID and name
