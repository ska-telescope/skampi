# -*- coding: utf-8 -*-
from tango import Database, DeviceProxy
from time import sleep

timeSleep = 30
for x in range(10):
    try:
        print ("Connecting to the databaseds")
        db = Database()
        break
    except:
        print ("Could not connect to the databaseds. Retry after " + str(timeSleep) + " seconds.")
        sleep(timeSleep)
print("Connected to the databaseds")