
from datetime import date
import random

import ska.cdm.messages.central_node.assign_resources as cdm_assign
from ska.cdm.messages.subarray_node.configure import ConfigureRequest
import ska.cdm.schemas as schemas
from ska.scripting import observingtasks
from ska.scripting.domain import Telescope, SubArray

import pytest

@pytest.mark.select
@pytest.mark.skamid_emulated
def test_ingest_visibilities_emulated():
 
    # Start up the telescope
    Telescope().start_up()

    def hacky_sleep(t, why):
        import time
        print(why)
        time.sleep(t)

    hacky_sleep(10, "give time to the telescope to *really* start up")

    # Choose IDs
    sbi_id = f"sbi-mvp01-{date.today():%Y%m%d}-{random.randint(0, 999999)}"
    pb_id = f"pb-mvp01-{date.today():%Y%m%d}-{random.randint(0, 999999)}"

    # Parse + send resource assignment
    res_request =  schemas.CODEC.loads(cdm_assign.AssignResourcesRequest, '''
    {
      "subarrayID": 1,
      "dish": { "receptorIDList": ["0001", "0002"] },
      "sdp": {
        "id": "'''+sbi_id+'''",
        "max_length": 100.0,
        "scan_types": [ { "id": "SPO-944-test",
            "coordinate_system": "ICRS", "ra": "21:08:47.92", "dec": "-88:57:22.9",
            "channels": [{
              "count": 744, "start": 0, "stride": 1,
              "freq_min": 0.35e9, "freq_max": 0.368e9, "link_map": []
            }]
          }
        ],
        "processing_blocks": [{
            "id": "'''+pb_id+'''",
            "workflow": {
                "id": "vis_receive", "type": "realtime", "version": "0.3.1"
            },
            "parameters": {
                "version": "1.5",
                "reception.outputfilename": "'''+pb_id+'''.ms", "reader.num_chan":4, "reader.num_repeats":1,
                "reader.num_timestamps": 0, "reader.start_chan": 0, "payload.method": "icd",
                "reception.datamodel": "sim-vis.ms", "pvc.path" : "/mnt",
                "reception.ring_heaps": 200, "results.push": true,
                "reception.receiver_port_start": 9000
            }
        }]
      }
    }''')
    observingtasks.assign_resources_from_cdm(1, res_request)

    hacky_sleep(40, "give time to k8s to make receiver workflow service hostname resolvable")

    # Parse + execute configuration request. The usual codec bits seem to
    # have a problem with custom fields and/or ADR-18, so we need to build
    # the command ourselves.
    TANGO_REGISTRY = observingtasks.TangoRegistry()
    subarray_node_fqdn = TANGO_REGISTRY.get_subarray_node(SubArray(1))
    cfg_command = observingtasks.Command(subarray_node_fqdn, 'Configure', '''
    {
      "pointing": { "target": { "name": "Polaris Australis", "system": "ICRS", "RA": "21:08:47.92", "dec": "-88:57:22.9" } },
      "dish": { "receiverBand": "1" },
      "csp": {
        "interface": "https://schema.skatelescope.org/ska-csp-configure/1.0",
        "subarray": { "subarrayName": "SPO-944 test" },
        "common": { "id": "'''+sbi_id+'''", "frequencyBand": "1", "subarrayID": 1 },
        "cbf": {
          "fsp": [{
              "fspID": 1, "functionMode": "CORR", "frequencySliceID": 1, "integrationTime": 1400, "corrBandwidth": 0,
              "transmission_source": "sim-vis.ms", "name_resolution_max_tries": 1000,
              "name_resolution_retry_period": 0.5, "transmission_rate": 1475000
          }]
        }
      },
      "sdp": { "scan_type": "SPO-944-test" },
      "tmc": { "scanDuration": 60.0 }
    }''')
    observingtasks.execute_configure_command(cfg_command)

    # Wait a bit for configuration
    hacky_sleep(30, "wait for configuration to settle?")

    # Execute a scan
    observingtasks.scan(SubArray('1'))

    # Wait a bit for the scan to (hopefully?) complete
    # TODO: Find out whether SDP has received visibilities here!
    hacky_sleep(60, "execute scan")
    
    # End scanning
    observingtasks.end(SubArray(1))

    # Release resources
    observingtasks.deallocate_resources(SubArray(1), release_all=True)

    # Move telescope to standby
    Telescope().standby()
