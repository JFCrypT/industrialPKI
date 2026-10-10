# Attack Test Script

`modifPLC.py` is the existing Modbus manipulation script used in the controlled testbed.

It is kept separate from the legitimate SCADA path so packet captures can compare normal control traffic, protected M262 traffic, and direct Modbus manipulation in the lab.

Run only against the authorized testbed.
