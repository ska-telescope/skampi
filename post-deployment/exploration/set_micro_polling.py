from tango import DeviceProxy

def main():
    devices = [
    'ska_mid/tm_subarray_node/1',
    'mid_csp/elt/subarray_01',
    'mid_csp_cbf/sub_elt/subarray_01',
    'mid_sdp/elt/subarray_1',
    'mid_csp/elt/subarray_01',
    ]
    for device in devices:
        p = DeviceProxy(device)
        p.poll_attribute('obsState',50)

if __name__ == "__main__":
    main()