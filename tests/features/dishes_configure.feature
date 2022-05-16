Feature: Configure Dishes for a subarrray scan
    
    @XTP-7119 @XTP-7117 @XTP-3324
    Scenario: Configure Dishes for a subarrray scan
        Given an set of dish masters currently assigned to a subarray in IDLE state
        Given a scan configuration with a particular target position and desired freq band
        When I configure those dishes in order to realise that scan configuration on the subarray
        Then the dishes shall be in a reported state actively tracking the desired source position at the desired frequency