# skamid-emulated

This is (and should remain)
a verbatim copy of the skamid umbrella chart,
except that instead of depending
on the mid-cbf chart to start the Mid.CBF subsystem
it depends on the mid-cbf-emulated chart.
The latter installs a device server for a simple, dummy CbfMaster device,
plus three CbfSubarray device servers
that use the cbf-sdp-emulator sender
to send data over to SDP.
