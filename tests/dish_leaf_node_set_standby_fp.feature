Feature: DishManager and DishLeafNode tests

    Scenario: Test dishleafnode SetStandbyFPMode command
        Given dish_manager dishMode reports STANDBY_LP
        When I issue SetStandbyFPMode on dish_leaf_node
        Then dish_manager dishMode and state should report STANDBY_FP and STANDBY
        And dish_structure operatingMode and powerState should report STANDBY_FP and FULL_POWER
        And spf operatingMode and powerState should report OPERATE and FULL_POWER
        And spfrx operatingMode should report DATA_CAPTURE
