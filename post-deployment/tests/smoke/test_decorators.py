from resources.test_support.sync_decorators import sync_assigned_resources,sync_configuration,sync_oet_configuration,sync_telescope_starting_up, \
    sync_sb_ending,sync_resources_releasing, sync_going_to_standby,sync_scanning,sync_going_to_standby,sync_oet_scanning
import mock
import pytest

    

@mock.patch('resources.test_support.sync_decorators.waiter')
@mock.patch('resources.test_support.sync_decorators.check_going_out_of_empty')
@pytest.mark.skamid
def test_sync_assigned_resources(check_going_out_of_empty,mock_waiter):
    # given
    mock_waiter_instance = mock_waiter.return_value
    # when I instantiate a context
    with sync_assigned_resources():
        # I first check that I am in the right state
        check_going_out_of_empty.assert_called()
        # I expect the waiter to be initialised
        mock_waiter_instance.set_wait_for_assign_resources.assert_called()
    #then after I have ran my code and exit the context
    # I expect a waiting to be called
    mock_waiter_instance.wait.assert_called()

@mock.patch('resources.test_support.sync_decorators.WaitConfigure')
@mock.patch('resources.test_support.sync_decorators.check_going_into_configure')
@pytest.mark.skamid
def test_sync_configuration(check_going_into_configure,WaitConfigure):
    # given
    WaitConfigure_instance = WaitConfigure.return_value
    # when I instantiate a context
    with sync_configuration():
        # I first check that I am in the right state
        check_going_into_configure.assert_called()
        # I expect the waiter to be initialised
        WaitConfigure.assert_called()
    #then after I have ran my code and exit the context
    # I expect a waiting to be called
    WaitConfigure_instance.wait.assert_called()


@mock.patch('resources.test_support.sync_decorators.WaitConfigure')
@mock.patch('resources.test_support.sync_decorators.check_going_into_configure')
@pytest.mark.skamid
def test_sync_oet_configuration(check_going_into_configure,WaitConfigure):
    # given
    WaitConfigure_instance = WaitConfigure.return_value
    # when I instantiate a context
    with sync_oet_configuration():
        # I first check that I am in the right state
        check_going_into_configure.assert_called()
        # I expect the waiter to be initialised
        WaitConfigure.assert_called()
    #then after I have ran my code and exit the context
    # I expect a waiting to be called
    WaitConfigure_instance.wait_oet.assert_called()

@mock.patch('resources.test_support.sync_decorators.waiter')
@mock.patch('resources.test_support.sync_decorators.check_coming_out_of_standby')
@pytest.mark.skamid
def test_sync_telescope_starting_up(check_coming_out_of_standby,mock_waiter):
    # given
    mock_waiter_instance = mock_waiter.return_value
    # when I instantiate a context
    with sync_telescope_starting_up():
        # I first check that I am in the right state
        check_coming_out_of_standby.assert_called()
        # I expect the waiter to be initialised
        mock_waiter_instance.set_wait_for_starting_up.assert_called()
    #then after I have ran my code and exit the context
    # I expect a waiting to be called
    mock_waiter_instance.wait.assert_called()

@mock.patch('resources.test_support.sync_decorators.waiter')
@mock.patch('resources.test_support.sync_decorators.check_going_out_of_configured')
@pytest.mark.skamid
def test_sync_sb_ending(check_going_out_of_configured,mock_waiter):
    # given
    mock_waiter_instance = mock_waiter.return_value
    # when I instantiate a context
    with sync_sb_ending():
        # I first check that I am in the right state
        check_going_out_of_configured.assert_called()
        # I expect the waiter to be initialised
        mock_waiter_instance.set_wait_for_ending_SB.assert_called()
    #then after I have ran my code and exit the context
    # I expect a waiting to be called
    mock_waiter_instance.wait.assert_called()

@mock.patch('resources.test_support.sync_decorators.waiter')
@mock.patch('resources.test_support.sync_decorators.check_going_into_empty')
@pytest.mark.skamid
def test_sync_resources_releasing(check_going_into_empty,mock_waiter):
    # given
    mock_waiter_instance = mock_waiter.return_value
    # when I instantiate a context
    with sync_resources_releasing():
        # I first check that I am in the right state
        #check_going_into_empty.assert_called()
        # I expect the waiter to be initialised
        mock_waiter_instance.set_wait_for_tearing_down_subarray.assert_called()
    #then after I have ran my code and exit the context
    # I expect a waiting to be called
    mock_waiter_instance.wait.assert_called()

@mock.patch('resources.test_support.sync_decorators.waiter')
@mock.patch('resources.test_support.sync_decorators.check_going_into_standby')
@pytest.mark.skamid
def test_sync_going_to_standby(check_going_into_standby,mock_waiter):
    # given
    mock_waiter_instance = mock_waiter.return_value
    # when I instantiate a context
    with sync_going_to_standby():
        # I first check that I am in the right state
        check_going_into_standby.assert_called()
        # I expect the waiter to be initialised
        mock_waiter_instance.set_wait_for_going_to_standby.assert_called()
    #then after I have ran my code and exit the context
    # I expect a waiting to be called
    mock_waiter_instance.wait.assert_called()

@mock.patch('resources.test_support.sync_decorators.WaitScanning')
@mock.patch('resources.test_support.sync_decorators.check_going_out_of_configured')
@pytest.mark.skamid
def test_sync_scanning(check_going_out_of_configured,WaitScanning):
    # given
    WaitScanning_instance = WaitScanning.return_value
    # when I instantiate a context
    with sync_scanning():
        # I first check that I am in the right state
        check_going_out_of_configured.assert_called()
        # I expect the waiter to be initialised
        WaitScanning.assert_called()
    #then after I have ran my code and exit the context
    # I expect a waiting to be called
    WaitScanning_instance.wait.assert_called()

@mock.patch('resources.test_support.sync_decorators.waiter')
@mock.patch('resources.test_support.sync_decorators.check_going_out_of_configured')
@pytest.mark.skamid
def test_sync_oet_scanning(check_going_out_of_configured,mock_waiter):
    # given
    mock_waiter_instance = mock_waiter.return_value
    # when I instantiate a context
    with sync_oet_scanning():
        # I first check that I am in the right state
        check_going_out_of_configured.assert_called()
        # I expect the waiter to be initialised
        mock_waiter_instance.set_wait_for_going_into_scanning.assert_called()
    #then after I have ran my code and exit the context
    # I expect a waiting to be called
    mock_waiter_instance.wait.assert_called()