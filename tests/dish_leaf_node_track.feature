Feature: DishManager and DishLeafNode tests

    Scenario: Test dishleafnode Track command
        Given dish_manager dishMode reports OPERATE
        And dish_manager pointingState reports READY
        When I issue Track on dish_leaf_node
        Then dish_manager dishMode should report OPERATE
        And dish_structure operatingMode POINT
        And spf operatingMode should report OPERATE
        And spfrx operatingMode should report DATA_CAPTURE
