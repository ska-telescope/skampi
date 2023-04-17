from resources.models.cbf_model.entry_point import cbf_low_configure_scan

from schema import Schema, Optional

configure_scan_schema = Schema(
    {
        "id": int,  # Configuration ID required by ska-tango-base classes
        Optional("common"): {Optional("subarrayID"): int},
        "lowcbf": {
            # Input to subarray from LFAA: stations, station_beams, frequencies
            "stations": {
                "stns": [
                    [
                        int,
                    ],
                ],  # stationID, substationID pairs
                "stn_beams": [
                    {
                        "beam_id": int,
                        "freq_ids": [
                            int,
                        ],
                        "boresight_dly_poly": str,
                    },
                ],
            },
            # Visibilities to be calculated
            Optional("vis"): {
                Optional("firmware"): str,
                "stn_beams": [
                    {"id": int, "dest_ip": str},
                ],
            },  # standard Correlation parameter list TBD
            # list of PST beams subarray is to calculate
            Optional("timing_beams"): {
                Optional("firmware"): str,
                "beams": [
                    {
                        "pst_beam_id": int,
                        "stn_beam_id": int,
                        "offset_dly_poly": str,
                        "jones": str,
                        "dest_ip": [
                            str,
                        ],
                        "dest_chans": [
                            int,
                        ],
                        Optional("stn_weights"): [
                            float,
                        ],
                        Optional("rfi_enable"): [
                            bool,
                        ],
                        Optional("rfi_static_chans"): [
                            int,
                        ],
                        Optional("rfi_dynamic_chans"): [
                            int,
                        ],
                        Optional("rfi_weighted"): float,
                    }
                ],
            },
            Optional("search_beams"): str,  # PSS parameter list TBD
            Optional("zooms"): str,  # zoom correlation parameter list TBD
        },
    },
)
"""ConfigureScan command schema"""


def test_schema():
    configure_scan_schema.validate(cbf_low_configure_scan)