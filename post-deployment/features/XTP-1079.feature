@VTS-228
Feature: Transaction ID logging
	#The start and end of every transaction should be logged with an ID.
	#If starting a new transaction, then a new ID must be generated.
	#This ID should be accessible for reuse for downstream transactions.

	Examples:
	| transaction_id_key | transaction_id | parameters                                                          | expected_transaction_id |
	|                    |                | {}                                                                  | < newly_generated >     |
	|                    |                | {"transaction_id": "", "config": "foo"}                             | < newly_generated >     |
	|                    |                | {"transaction_id": "abc1234", "config": "foo"}                      | abc1234                 |
	|                    | xyz1234        | {"transaction_id": "abc1234", "config": "foo"}                      | xyz1234                 |
	| txn_id             |                | {"txn_id": "abc1234", "config": "foo"}                              | abc1234                 |
	| txn_id             | xyz1234        | {"txn_id": "abc1234", "config": "foo"}                              | xyz1234                 |
	| txn_id             | xyz1234        | {"txn_id": "abc1234", "config": "foo", "transaction_id": "def1234"} | xyz1234                 |


	@XTP-1080 @XTP-1079 @PI8
	Scenario Outline: Executing a transaction that succeeds
		Given an example transaction logging application
		When executing a successful transaction named <command_name> with <parameters> and <transaction_id> and <transaction_id_key>
		Then the start of the transaction is logged with the <expected_transaction_id>, <command_name> and <parameters>
		And the end of the transaction is logged with the <expected_transaction_id> and <command_name>

		Examples:
		| command_name |
		| Configure    |


	@XTP-1081 @XTP-1079 @PI8
	Scenario Outline: Executing a transaction that fails
		Given an example transaction logging application
		When executing a transaction named <command_name> with <parameters> and <transaction_id> and <transaction_id_key> that raises an exception
		Then the start of the transaction is logged with the <expected_transaction_id>, <command_name> and <parameters>
		And the exception message is logged with the <expected_transaction_id> and <command_name>
		And the end of the transaction is logged with the <expected_transaction_id> and <command_name>

		Examples:
		| command_name    |
		| RaisesException |