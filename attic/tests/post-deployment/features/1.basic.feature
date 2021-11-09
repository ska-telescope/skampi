@fast
@common
Scenario: Call Command and test attribute
	Given a device called sys/tg_test/1
	When I call the command State()
	Then the attribute State is RUNNING

@fast
@common
Scenario: Call Command and check result
	Given a device called sys/tg_test/1
	When I call the command State()
	Then the result is RUNNING

@fast
@common
Scenario: Call Command DevString
	Given a device called sys/tg_test/1
	When I call the command DevString(ciao ciao)
	Then the result is ciao ciao

@fast
@common
Scenario: Call Command DevShort
	Given a device called sys/tg_test/1
	When I call the command DevShort(1)
	Then the result is 1

@fast
@common
Scenario: Call Command DevLong
	Given a device called sys/tg_test/1
	When I call the command DevLong(1)
	Then the result is 1

@fast
@common
Scenario: Call Command DevUShort
	Given a device called sys/tg_test/1
	When I call the command DevUShort(1)
	Then the result is 1

@fast
@common
Scenario: Call Command DevULong
	Given a device called sys/tg_test/1
	When I call the command DevULong(1)
	Then the result is 1

@fast
@common
Scenario: Call Command DevLong64
	Given a device called sys/tg_test/1
	When I call the command DevLong64(1)
	Then the result is 1

@fast
@common
Scenario: Call Command DevULong64
	Given a device called sys/tg_test/1
	When I call the command DevULong64(1)
	Then the result is 1

# Scenario: Call Command DevFloat
# 	Given a device called sys/tg_test/1
# 	When I call the command DevFloat(1.2)
# 	Then the result is 1.2

# Scenario: Call Command DevDouble
# 	Given a device called sys/tg_test/1
# 	When I call the command DevDouble(1.2)
# 	Then the result is 1.2

# Scenario: Call Command DevBoolean
# 	Given a device called sys/tg_test/1
# 	When I call the command DevBoolean(false)
# 	Then the result is false