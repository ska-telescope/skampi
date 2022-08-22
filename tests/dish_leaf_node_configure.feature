Feature: Dish LMC acceptance tests

    Background:
        Given dish_leaf_node, dish_manager, dish_structure, spf, spfrx devices

        Scenario: Test dishleafnode Configure command
            Given dish_manager dishMode reports STANDBY_FP
            When I issue Configure command on dish_leaf_node
            Then dish_manager dishMode should report CONFIG briefly
            And dish_structure indexerPosition should report B2
            And spf bandInFocus should report B2
            And spfrx operatingMode should report DATA_CAPTURE
            And spfrx configuredBand should report B2
            And dish_manager configuredBand should report B2
            And dish_manager dishMode should report STANDBY_FP