# import unittest.mock as mock
# from resources.test_support.oet_helpers import ScriptExecutor, REST_CLIENT
#
# REST_START_RESPONSE = """"""
#
# REST_CREATE_RESPONSE = """"""
#
# REST_LIST_RESPONSE = """"""
#
# class TestScriptExecutor:
#
#     def test_parse_rest_response(self):
#         pass
#
#     def test_parse_rest_start_response(self):
#         pass
#
#     @mock.patch.object(REST_CLIENT, 'create')
#     @mock.patch.object(ScriptExecutor, 'parse_rest_response')
#     def test_create_script(self):
#         ScriptExecutor().create_script('file:///fake_script.py')
#         REST_CLIENT.assert_called_once_with('file:///fake_script.py')
#
#     @mock.patch.object(REST_CLIENT, 'start')
#     @mock.patch.object(ScriptExecutor, 'parse_rest_start_response')
#     def test_start_script(self):
#         ScriptExecutor().start_script('file:///fake_script.py')
#         REST_CLIENT.assert_called_once_with('file:///fake_script.py')
#
#     @mock.patch.object(REST_CLIENT, 'list')
#     @mock.patch.object(ScriptExecutor, 'parse_rest_response')
#     def test_list_scripts(self):
#         ScriptExecutor().list_scripts()
#         REST_CLIENT.assert_called_once_with(run_abort=False)
#
#     @mock.patch.object(REST_CLIENT, 'stop')
#     def test_stop_script(self):
#         ScriptExecutor().stop_script()
#         REST_CLIENT.assert_called_once_with(run_abort=False)
#
