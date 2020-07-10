from tango_simlib.utilities.validate_device import check_single_dict_differences

# just check that tango-simlib works okay
dict_A = {
    'disp_level': 'OPERATOR',
    'doc_in': 'ON/OFF',
    'doc_out': 'Uninitialised',
    'dtype_in': 'DevBoolean',
    'dtype_out': 'DevVoid',
    'name': 'Capture'
    }

dict_B = {
    'disp_level': 'OPERATOR',
    'doc_in': 'ON/OFF',
    'doc_out': 'Uninitialised',
    'dtype_in': 'DevBoolean',
    'dtype_out': 'DevVoid',
    'name': 'Capture'
    }

issues = check_single_dict_differences(dict_A, dict_B, "Command", True)
assert len(issues) == 2 # make it fail
