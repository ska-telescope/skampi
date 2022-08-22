Feature: DishManager and DishLeafNode tests

    Background:
        Given dish_leaf_node, dish_manager, dish_structure, spf, spfrx devices

        Scenario: Test dishleafnode SetOperateMode command
            Given dish_manager dishMode reports STANDBY_FP
            # And dish_manager configuredBand reports B2
            When I issue SetOperateMode command on dish_leaf_node
            Then dish_manager dishMode should report OPERATE
            # And the dish state should report <dish_state>
            # And dish_structure operatingMode and powerState should report <ds_operating_mode> and <ds_power_state>
            # And spf operatingMode and powerState should report <spf_operating_mode> and <spf_power_state>
            # And spfrx operatingMode should report <spfrx_operating_mode>