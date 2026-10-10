#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Dual Modbus TCP emulator for the SCADA.
Compatible with PyModbus 3.13+ / 3.14+ / 3.15.

Emulates:
- Schneider M262
- Delta

IMPORTANT:
PyModbus 3.13+ removed getValues()/setValues() from the datastore.
This version uses the current server methods:
    await server.async_getValues(...)
    await server.async_setValues(...)

External SCADA addresses do NOT change.
"""

import asyncio
import time
from dataclasses import dataclass

from pymodbus.datastore import (
    ModbusDeviceContext,
    ModbusSequentialDataBlock,
    ModbusServerContext,
)
from pymodbus.server import ModbusTcpServer


HOST = "0.0.0.0"

M262_PORT = 1502
M262_UNIT_ID = 255

DELTA_PORT = 1503
DELTA_UNIT_ID = 1

# Newer PyModbus versions do not accept a data block starting at 0.
# Start at 1; ServerContext preserves the external Modbus offsets.
COIL_COUNT = 65535


# ============================================================
# EMULATOR MODBUS MAP
# ============================================================

# M262
M262_TURN_ON = 100
M262_EMERGENCY = 101
M262_HACKED = 102
M262_RED = 110
M262_YELLOW = 111
M262_GREEN = 112
M262_RUN_STATE = 113

# Delta
DELTA_TURN_ON = 3120
DELTA_EMERGENCY = 3121
DELTA_HACKED = 3122
DELTA_RED = 3130
DELTA_YELLOW = 3131
DELTA_GREEN = 3132
DELTA_RUN_STATE = 3133


@dataclass
class PLCMap:
    name: str
    unit_id: int
    turn_on: int
    emergency: int
    hacked: int
    red: int
    yellow: int
    green: int
    run_state: int


def make_context(unit_id: int):
    coils = ModbusSequentialDataBlock(1, [False] * COIL_COUNT)
    device = ModbusDeviceContext(co=coils)

    return ModbusServerContext(
        devices={unit_id: device},
        single=False,
    )


class VirtualPLC:
    def __init__(self, plc_map: PLCMap):
        self.map = plc_map
        self.server = None
        self.mode = None
        self.mode_started = time.monotonic()

    def attach_server(self, server):
        self.server = server

    async def get_coil(self, address: int) -> bool:
        values = await self.server.async_getValues(
            self.map.unit_id,
            1,  # FC01 / coils
            int(address),
            1,
        )
        return bool(values[0])

    async def set_coil(self, address: int, value: bool):
        await self.server.async_setValues(
            self.map.unit_id,
            5,  # FC05 / coil space
            int(address),
            [bool(value)],
        )

    async def set_outputs(self, red: bool, yellow: bool, green: bool):
        await self.set_coil(self.map.red, red)
        await self.set_coil(self.map.yellow, yellow)
        await self.set_coil(self.map.green, green)

    async def determine_mode(self):
        hacked = await self.get_coil(self.map.hacked)
        emergency = await self.get_coil(self.map.emergency)

        if hacked:
            return "hacked"
        if emergency:
            return "emergency"
        return "normal"

    async def scan(self):
        # turn_on = 0 -> RUN
        # turn_on = 1 -> STOP
        running = not await self.get_coil(self.map.turn_on)
        await self.set_coil(self.map.run_state, running)

        if not running:
            await self.set_outputs(False, False, False)
            self.mode = "stopped"
            self.mode_started = time.monotonic()
            return

        new_mode = await self.determine_mode()

        if new_mode != self.mode:
            self.mode = new_mode
            self.mode_started = time.monotonic()

        elapsed = time.monotonic() - self.mode_started

        if self.mode == "normal":
            t = elapsed % 20.0
            if t < 8.0:
                await self.set_outputs(False, False, True)
            elif t < 10.0:
                await self.set_outputs(False, True, True)
            elif t < 18.0:
                await self.set_outputs(True, False, False)
            else:
                await self.set_outputs(True, True, False)

        elif self.mode == "emergency":
            t = elapsed % 2.0
            await self.set_outputs(t < 1.0, False, False)

        elif self.mode == "hacked":
            t = elapsed % 1.4
            if t < 0.2:
                await self.set_outputs(True, False, False)
            elif t < 0.4:
                await self.set_outputs(True, True, False)
            elif t < 0.6:
                await self.set_outputs(False, True, True)
            elif t < 0.8:
                await self.set_outputs(False, False, True)
            elif t < 1.0:
                await self.set_outputs(False, False, False)
            elif t < 1.2:
                await self.set_outputs(False, True, True)
            else:
                await self.set_outputs(True, True, False)


async def plc_scan_loop(m262: VirtualPLC, delta: VirtualPLC):
    last_print = 0.0

    while True:
        await m262.scan()
        await delta.scan()

        now = time.monotonic()

        if now - last_print >= 1.0:
            last_print = now

            async def state(p):
                r = int(await p.get_coil(p.map.red))
                y = int(await p.get_coil(p.map.yellow))
                g = int(await p.get_coil(p.map.green))
                return (
                    f"{p.map.name}: "
                    f"mode={p.mode:<9} "
                    f"R={r} Y={y} G={g}"
                )

            print(await state(m262))
            print(await state(delta))
            print("-" * 70)

        await asyncio.sleep(0.02)


async def main():
    m262 = VirtualPLC(
        PLCMap(
            name="M262",
            unit_id=M262_UNIT_ID,
            turn_on=M262_TURN_ON,
            emergency=M262_EMERGENCY,
            hacked=M262_HACKED,
            red=M262_RED,
            yellow=M262_YELLOW,
            green=M262_GREEN,
            run_state=M262_RUN_STATE,
        )
    )

    delta = VirtualPLC(
        PLCMap(
            name="Delta",
            unit_id=DELTA_UNIT_ID,
            turn_on=DELTA_TURN_ON,
            emergency=DELTA_EMERGENCY,
            hacked=DELTA_HACKED,
            red=DELTA_RED,
            yellow=DELTA_YELLOW,
            green=DELTA_GREEN,
            run_state=DELTA_RUN_STATE,
        )
    )

    m262_server = ModbusTcpServer(
        context=make_context(M262_UNIT_ID),
        address=(HOST, M262_PORT),
    )

    delta_server = ModbusTcpServer(
        context=make_context(DELTA_UNIT_ID),
        address=(HOST, DELTA_PORT),
    )

    m262.attach_server(m262_server)
    delta.attach_server(delta_server)

    # Initial state: both PLCs in STOP.
    await m262.set_coil(M262_TURN_ON, True)
    await delta.set_coil(DELTA_TURN_ON, True)

    print()
    print("=" * 70)
    print("DUAL PLC EMULATOR - MODBUS TCP")
    print("=" * 70)
    print()
    print("M262")
    print("  SCADA IP:      127.0.0.1")
    print(f"  Port:          {M262_PORT}")
    print(f"  Unit ID:       {M262_UNIT_ID}")
    print(f"  START/STOP:    {M262_TURN_ON}")
    print(f"  EMERGENCY:     {M262_EMERGENCY}")
    print(f"  HACKED:        {M262_HACKED}")
    print(f"  RED:           {M262_RED}")
    print(f"  YELLOW:        {M262_YELLOW}")
    print(f"  GREEN:         {M262_GREEN}")
    print()
    print("DELTA")
    print("  SCADA IP:      127.0.0.1")
    print(f"  Port:          {DELTA_PORT}")
    print(f"  Unit ID:       {DELTA_UNIT_ID}")
    print(f"  START/STOP:    {DELTA_TURN_ON}")
    print(f"  EMERGENCY:     {DELTA_EMERGENCY}")
    print(f"  HACKED:        {DELTA_HACKED}")
    print(f"  RED:           {DELTA_RED}")
    print(f"  YELLOW:        {DELTA_YELLOW}")
    print(f"  GREEN:         {DELTA_GREEN}")
    print()
    print("Both PLCs start in STOP.")
    print("Use START from the SCADA.")
    print("Press Ctrl+C to stop.")
    print("=" * 70)
    print()

    await asyncio.gather(
        m262_server.serve_forever(),
        delta_server.serve_forever(),
        plc_scan_loop(m262, delta),
    )


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nEmulator stopped.")
