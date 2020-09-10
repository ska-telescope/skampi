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

	
	@XTP-1081 @XTP-1079 @PI8
	Scenario Outline: Continuing an existing transaction
		Given an example transaction logging application
		And a transaction ID is already present
		When executing a transaction named <command_name>
		Then that transaction ID is used
		And start of transaction is logged including that transaction ID and name <command_name>
		And end of transaction is logged including that transaction ID and name <command_name>
		
		Examples:
		| command_name |
		| Configure    |
			

	
	@XTP-1084 @XTP-1079 @PI8
	Scenario Outline: Executing a transaction with parameters
		Given an example transaction logging application
		And a transaction ID is already present
		And the transaction parameters are <parameters>
		When executing a transaction named <command_name>
		Then start of transaction is logged including that transaction ID and name <command_name> and <parameters>
		
		Examples:
		| command_name | parameters                                     |
		| Configure    | {'transaction_id': 'abc1234', 'config': 'foo'} |
			

	
	@XTP-1085 @XTP-1079 @PI8
	Scenario Outline: Executing a transaction that fails
		Given an example transaction logging application
		And a transaction ID is already present
		When executing a transaction named <command_name>
		And an exception occurs 
		Then end of transaction is logged including that transaction ID and name <command_name> and the error message
		
		Examples:
		| command_name |
		| Configure    |