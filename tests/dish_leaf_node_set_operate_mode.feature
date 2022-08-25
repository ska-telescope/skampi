Feature: DishManager and DishLeafNode tests

    Scenario: Test dishleafnode SetOperateMode command
        Given dish_manager dishMode reports STANDBY_FP
        And dish_manager configuredBand reports B2
        When I issue SetOperateMode command on dish_leaf_node
        Then dish_manager dishMode should report OPERATE