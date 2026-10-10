# Controlled Attack Test Script

`modifPLC.py` is retained as a controlled Modbus manipulation tool for the authorized laboratory testbed.

Its purpose is to compare:

```text
legitimate SCADA traffic
protected M262-path traffic
plaintext Delta-path traffic
direct Modbus manipulation in the lab
```

Use it only against systems for which explicit authorization exists.

This tool is not part of the PKI deployment path.
