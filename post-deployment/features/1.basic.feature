@pytest.mark.fast
Scenario: Call Command and test attribute
	Given a device called sys/tg_test/1
	When I call the command State()
	Then the attribute State is RUNNING

@pytest.mark.fast
Scenario: Call Command and check result
	Given a device called sys/tg_test/1
	When I call the command State()
	Then the result is RUNNING

@pytest.mark.fast
Scenario: Call Command DevString
	Given a device called sys/tg_test/1
	When I call the command DevString(ciao ciao)
	Then the result is ciao ciao

@pytest.mark.fast
Scenario: Call Command DevShort
	Given a device called sys/tg_test/1
	When I call the command DevShort(1)
	Then the result is 1

@pytest.mark.fast
Scenario: Call Command DevLong
	Given a device called sys/tg_test/1
	When I call the command DevLong(1)
	Then the result is 1

@pytest.mark.fast
Scenario: Call Command DevUShort
	Given a device called sys/tg_test/1
	When I call the command DevUShort(1)
	Then the result is 1

@pytest.mark.fast
Scenario: Call Command DevULong
	Given a device called sys/tg_test/1
	When I call the command DevULong(1)
	Then the result is 1

@pytest.mark.fast
Scenario: Call Command DevLong64
	Given a device called sys/tg_test/1
	When I call the command DevLong64(1)
	Then the result is 1

@pytest.mark.fast
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