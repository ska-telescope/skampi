CONFIGURE ALARM IN SKAMPI
************************

Note: Run Mid On Demand Job in SKAMPI and after it run successfully then follow following steps

CONFIGURE AND TEST ALARM USING IPYTHON Terminal
-----------------------------------------------


* Copy KUBECONFIG Locally using curl command for completed Job
    Example: ``curl https://artefact.skao.int/repository/k8s-ci-creds-internal/k8s-ci-svc-ska-skampi-hm-157-ci-ska-skampi-hm-157-mid-conf --output KUBECONFIG)

* Get list of Pods
   .. code-block:: 
    
      kubectl --kubeconfig=KUBECONFIG get pods

* Open new tab in Terminal and run alarm cli viewer
   .. code-block:: 

      kubectl --kubeconfig=KUBECONFIG exec -it <replace this with alarm cli viewer pod name> -- /bin/bash -c "/usr/bin/python data/cli_viewer.py --ah=alarm/handler/01"

* Open another Tab in Terminal and login to one of the pod. For example login to cli viewer pod
   .. code-block::  
        
        kubectl --kubeconfig=KUBECONFIG exec -it <replace this with alarm cli viewer pod name> -- /bin/bash

* Start ipython Terminal

* In ipython terminal Configure alarm as follows 
   .. code-block::
        
        import tango
        alarm_handler = tango.DeviceProxy("alarm/handler/01")
            
        # Configure alarm for subarray healthState DEGRADED state as follow
        alarm_handler.command_inout("Load","tag=subarraynode_healthstate;formula=(ska_mid/tm_subarray_node/1/healthState == 1);priority=log;group=none;message=(\"alarm for subarray node test mode\")")
        # When above alarm is configured then whenever subarray health state is 1 (DEGRADED) then alarm will be raised

        # To check alarm list use alarmSummary attribute
        print(alarm_handler.alarmSummary)

* After Alarm is configured then raised Alarms will be displayed in alarm cli viewer table.
  
  .. image:: alarm_cli.png
     :alt: Alarm Cli Viewer


CONFIGURE AND TEST ALARM USING TARANTA UI
-----------------------------------------

* Execute Load command on Alarm device to configure alarms.
  
  .. image:: alarm_load.png
     :alt: Load Alarm in Taranta

* Check alarmSummary Spectrum Attribute of Alarm Handler device which display list of configured alarms.
  
  .. image:: alarm_display.png
     :alt: View Alarm in Taranta
  
  
