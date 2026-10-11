#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import ssl
import threading
import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path

from pymodbus.client import ModbusTcpClient, ModbusTlsClient


CONFIG_FILE = Path(__file__).with_name("scada_dual_config.json")
PROJECT_ROOT = Path(__file__).resolve().parent.parent

DEFAULT_CONFIG = {
    "m262": {
        "name": "Schneider M262",
        "ip": "192.168.0.24",
        "port": 802,
        "device_id": 255,
        "transport": "tls",
        "tls_ca": "pki/ca/certs/rootCA.crt",
        "tls_cert": "pki/scada/certs/scada.crt",
        "tls_key": "pki/scada/private/scada.key",
        "tls_check_hostname": True,
        "addr_turn_on": "",
        "addr_emergency": "",
        "addr_hacked": "",
        "addr_red": "",
        "addr_yellow": "",
        "addr_green": "",
        "start_value": 0,
        "stop_value": 1,
        "emergency_on_value": 1,
        "emergency_off_value": 0,
        "hacked_on_value": 1,
        "hacked_off_value": 0,
    },
    "delta": {
        "name": "Delta",
        "ip": "192.168.0.15",
        "port": 502,
        "device_id": 1,
        "transport": "tcp",
        "addr_turn_on": 1284,
        "addr_emergency": 1288,
        "addr_hacked": 1286,
        "addr_red": 1281,
        "addr_yellow": 1282,
        "addr_green": 1283,
        "start_value": 1,
        "stop_value": 0,
        "emergency_on_value": 1,
        "emergency_off_value": 0,
        "hacked_on_value": 1,
        "hacked_off_value": 0,
    },
    "poll_ms": 500,
}


def deep_merge(base, new):
    out = {}
    for k, v in base.items():
        if isinstance(v, dict):
            out[k] = deep_merge(v, new.get(k, {}) if isinstance(new, dict) else {})
        else:
            out[k] = new.get(k, v) if isinstance(new, dict) else v
    if isinstance(new, dict):
        for k, v in new.items():
            if k not in out:
                out[k] = v
    return out


def load_config():
    if CONFIG_FILE.exists():
        try:
            data = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
            return deep_merge(DEFAULT_CONFIG, data)
        except Exception:
            pass
    return json.loads(json.dumps(DEFAULT_CONFIG))


def save_config(cfg):
    CONFIG_FILE.write_text(
        json.dumps(cfg, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )


class ModbusNode:
    def __init__(self):
        self.client = None
        self.device_id = 1
        self.lock = threading.Lock()

    def connect(self, cfg, ip, port, device_id):
        with self.lock:
            self.close()
            self.device_id = int(device_id)
            transport = str(cfg.get("transport", "tcp")).lower()

            if transport == "tls":
                ca_file = PROJECT_ROOT / cfg.get("tls_ca", "pki/ca/certs/rootCA.crt")
                cert_file = PROJECT_ROOT / cfg.get("tls_cert", "pki/scada/certs/scada.crt")
                key_file = PROJECT_ROOT / cfg.get("tls_key", "pki/scada/private/scada.key")

                ctx = ssl.create_default_context(ssl.Purpose.SERVER_AUTH, cafile=str(ca_file))
                ctx.load_cert_chain(certfile=str(cert_file), keyfile=str(key_file))
                ctx.minimum_version = ssl.TLSVersion.TLSv1_2
                ctx.check_hostname = bool(cfg.get("tls_check_hostname", True))

                self.client = ModbusTlsClient(
                    ip, port=int(port), sslctx=ctx
                )
            else:
                self.client = ModbusTcpClient(ip, port=int(port))

            return bool(self.client.connect())

    def close(self):
        try:
            if self.client:
                self.client.close()
        except Exception:
            pass
        self.client = None

    def write_coil(self, address, value):
        """Single FC05 write. Kept for Delta."""
        with self.lock:
            if not self.client:
                raise RuntimeError("No Modbus connection")

            try:
                result = self.client.write_coil(
                    int(address), bool(value), device_id=self.device_id
                )
            except TypeError:
                result = self.client.write_coil(
                    int(address), bool(value), slave=self.device_id
                )

            if result.isError():
                raise RuntimeError(str(result))

    def write_m262_coil(self, address, value):
        """
        M262 digital-output write using FC15.

        Schneider documents FC15 (Write Multiple Coils / digital outputs)
        for the embedded M262 Modbus TCP server. FC05 is not listed as a
        supported embedded-server request, so even a single-bit write is
        sent with write_coils(..., [value]).
        """
        with self.lock:
            if not self.client:
                raise RuntimeError("No Modbus connection")

            try:
                result = self.client.write_coils(
                    int(address), [bool(value)], device_id=self.device_id
                )
            except TypeError:
                result = self.client.write_coils(
                    int(address), [bool(value)], slave=self.device_id
                )

            if result.isError():
                raise RuntimeError(str(result))

    def read_coil(self, address):
        with self.lock:
            if not self.client:
                raise RuntimeError("No Modbus connection")

            try:
                result = self.client.read_coils(
                    int(address), count=1, device_id=self.device_id
                )
            except TypeError:
                result = self.client.read_coils(
                    int(address), count=1, slave=self.device_id
                )

            if result.isError():
                raise RuntimeError(str(result))
            return bool(result.bits[0])


class PLCPanel(ttk.LabelFrame):
    def __init__(self, master, key, cfg, on_change):
        super().__init__(master, text=cfg["name"], padding=1)

        self.key = key
        self.cfg = cfg
        self.on_change = on_change
        self.node = ModbusNode()
        self.connected = False

        self.red_on = False
        self.yellow_on = False
        self.green_on = False

        self.ip_var = tk.StringVar(value=str(cfg["ip"]))
        self.port_var = tk.StringVar(value=str(cfg["port"]))
        self.id_var = tk.StringVar(value=str(cfg["device_id"]))

        self.addr_turn_on = tk.StringVar(value=str(cfg["addr_turn_on"]))
        self.addr_emergency = tk.StringVar(value=str(cfg["addr_emergency"]))
        self.addr_hacked = tk.StringVar(value=str(cfg["addr_hacked"]))
        self.addr_red = tk.StringVar(value=str(cfg["addr_red"]))
        self.addr_yellow = tk.StringVar(value=str(cfg["addr_yellow"]))
        self.addr_green = tk.StringVar(value=str(cfg["addr_green"]))

        self._build()

    def _build(self):
        self.columnconfigure(1, weight=1)

        row = 0
        for label, var in (
            ("IP", self.ip_var),
            ("Port", self.port_var),
            ("Unit ID", self.id_var),
        ):
            ttk.Label(self, text=label).grid(row=row, column=0, sticky="w", pady=0)
            ttk.Entry(self, textvariable=var, width=14).grid(
                row=row, column=1, sticky="ew", padx=(6, 0), pady=0
            )
            row += 1

        self.conn_label = ttk.Label(self, text="DISCONNECTED")
        self.conn_label.grid(row=row, column=0, sticky="w", pady=(0, 0))

        self.connect_btn = ttk.Button(
            self, text="CONNECT", command=self.toggle_connection
        )
        self.connect_btn.grid(
            row=row, column=1, sticky="ew", padx=(6, 0), pady=(0, 0)
        )
        row += 1

        ttk.Separator(self).grid(
            row=row, column=0, columnspan=2, sticky="ew", pady=0
        )
        row += 1

        ttk.Label(self, text="START/STOP").grid(
            row=row, column=0, sticky="w", pady=0
        )
        ttk.Entry(self, textvariable=self.addr_turn_on, width=12).grid(
            row=row, column=1, sticky="ew", padx=(6, 0), pady=0
        )
        row += 1

        ttk.Label(self, text="EMERGENCY").grid(
            row=row, column=0, sticky="w", pady=0
        )
        ttk.Entry(self, textvariable=self.addr_emergency, width=12).grid(
            row=row, column=1, sticky="ew", padx=(6, 0), pady=0
        )
        row += 1

        ttk.Button(
            self,
            text="TURN ON / START",
            command=lambda: self.command_async(
                "START",
                self.addr_turn_on,
                bool(self.cfg["start_value"])
            ),
        ).grid(row=row, column=0, columnspan=2, sticky="ew", pady=(0, 0))
        row += 1

        ttk.Button(
            self,
            text="TURN OFF / STOP",
            command=lambda: self.command_async(
                "STOP",
                self.addr_turn_on,
                bool(self.cfg["stop_value"])
            ),
        ).grid(row=row, column=0, columnspan=2, sticky="ew", pady=0)
        row += 1

        ttk.Button(
            self,
            text="EMERGENCY ON",
            command=lambda: self.command_async(
                "EMERGENCY ON",
                self.addr_emergency,
                bool(self.cfg["emergency_on_value"])
            ),
        ).grid(row=row, column=0, columnspan=2, sticky="ew", pady=(0, 0))
        row += 1

        ttk.Button(
            self,
            text="EMERGENCY OFF",
            command=lambda: self.command_async(
                "EMERGENCY OFF",
                self.addr_emergency,
                bool(self.cfg["emergency_off_value"])
            ),
        ).grid(row=row, column=0, columnspan=2, sticky="ew", pady=0)
        row += 1

        self.last_action = ttk.Label(self, text="No commands")
        self.last_action.grid(
            row=row, column=0, columnspan=2, sticky="w", pady=(0, 0)
        )

    @staticmethod
    def parse_addr(var):
        txt = var.get().strip()
        if txt == "":
            raise ValueError("Modbus address is not configured")
        return int(txt)

    def toggle_connection(self):
        if self.connected:
            self.node.close()
            self.connected = False
            self.conn_label.configure(text="DISCONNECTED")
            self.connect_btn.configure(text="CONNECT")
            self.on_change()
            return

        try:
            ok = self.node.connect(
                self.cfg,
                self.ip_var.get().strip(),
                int(self.port_var.get()),
                int(self.id_var.get()),
            )
        except Exception as exc:
            messagebox.showerror(self.cfg["name"], str(exc))
            return

        self.connected = ok

        if ok:
            self.conn_label.configure(text="CONNECTED")
            self.connect_btn.configure(text="DISCONNECT")
            self.last_action.configure(text="Modbus connection established")
        else:
            self.conn_label.configure(text="ERROR")
            messagebox.showerror(
                self.cfg["name"],
                "Could not connect to PLC"
            )

        self.on_change()

    def command_async(self, name, addr_var, value):
        if not self.connected:
            messagebox.showwarning(
                self.cfg["name"],
                "Connect to the PLC first"
            )
            return

        try:
            addr = self.parse_addr(addr_var)
        except Exception as exc:
            messagebox.showwarning(self.cfg["name"], str(exc))
            return

        def worker():
            try:
                if self.key == "m262":
                    self.node.write_m262_coil(addr, value)
                else:
                    self.node.write_coil(addr, value)

                self.after(
                    0,
                    lambda: self.last_action.configure(
                        text=f"{name}: coil {addr} ← {int(value)}"
                    ),
                )
            except Exception as exc:
                self.after(
                    0,
                    lambda e=str(exc): messagebox.showerror(
                        self.cfg["name"], e
                    ),
                )
            self.after(0, self.on_change)

        threading.Thread(target=worker, daemon=True).start()

    def poll(self):
        if not self.connected:
            return

        for attr, var in (
            ("red_on", self.addr_red),
            ("yellow_on", self.addr_yellow),
            ("green_on", self.addr_green),
        ):
            try:
                setattr(self, attr, self.node.read_coil(self.parse_addr(var)))
            except Exception:
                pass

    def export_config(self):
        self.cfg.update({
            "ip": self.ip_var.get().strip(),
            "port": int(self.port_var.get()),
            "device_id": int(self.id_var.get()),
            "addr_turn_on": self.addr_turn_on.get().strip(),
            "addr_emergency": self.addr_emergency.get().strip(),
            "addr_hacked": self.addr_hacked.get().strip(),
            "addr_red": self.addr_red.get().strip(),
            "addr_yellow": self.addr_yellow.get().strip(),
            "addr_green": self.addr_green.get().strip(),
        })
        return self.cfg


class App(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("Dual SCADA - M262 + Delta")
        self.geometry("1360x710")
        self.minsize(1100, 640)

        self.cfg = load_config()
        self.running = True

        self.protocol("WM_DELETE_WINDOW", self.on_close)

        self._build_ui()
        self.after(300, self.poll_loop)

    def _build_ui(self):
        top = ttk.Frame(self, padding=(8, 3))
        top.pack(fill="x")

        ttk.Label(
            top,
            text="SCADA · M262 + DELTA · MODBUS TCP/TLS",
            font=("Segoe UI", 17, "bold"),
        ).pack(side="left")

        ttk.Button(
            top,
            text="⚙ Maintenance",
            command=self.toggle_maintenance,
        ).pack(side="right")

        self.sync_status = ttk.Label(top, text="")
        self.sync_status.pack(side="right", padx=(0, 10))

        ttk.Button(
            top,
            text="SYNCHRONIZE",
            command=self.synchronize_existing_programs,
        ).pack(side="right", padx=(0, 8))

        body = ttk.Frame(self, padding=(8, 0, 8, 0))
        body.pack(fill="both", expand=True)

        # Fixed sidebar: both PLC panels remain fully visible without scrolling.
        sidebar = ttk.Frame(body, width=305)
        sidebar.pack(side="left", fill="y", padx=(0, 8))
        sidebar.pack_propagate(False)

        # Main monitoring area.
        monitor = ttk.Frame(body)
        monitor.pack(side="left", fill="both", expand=True)

        self.m262 = PLCPanel(
            sidebar, "m262", self.cfg["m262"], self.draw_scene
        )
        self.m262.pack(fill="x", pady=(0, 0))

        self.delta = PLCPanel(
            sidebar, "delta", self.cfg["delta"], self.draw_scene
        )
        self.delta.pack(fill="both", expand=True)

        # Maintenance opens in a separate window.
        self.maint_window = None

        monitor_box = ttk.LabelFrame(
            monitor, text="GENERAL MONITORING", padding=6
        )
        monitor_box.pack(fill="both", expand=True)

        self.canvas = tk.Canvas(
            monitor_box,
            bg="#8aa5b6",
            highlightthickness=0,
        )
        self.canvas.pack(fill="both", expand=True)
        self.canvas.bind("<Configure>", lambda e: self.draw_scene())

    def _build_maintenance_panel(self, parent, panel):
        f = ttk.LabelFrame(
            parent,
            text=panel.cfg["name"],
            padding=10,
        )
        f.pack(side="left", fill="both", expand=True, padx=8, pady=8)

        rows = [
            ("HACKED address", panel.addr_hacked),
            ("Red light", panel.addr_red),
            ("Yellow light", panel.addr_yellow),
            ("Green light", panel.addr_green),
        ]

        for r, (label, var) in enumerate(rows):
            ttk.Label(f, text=label).grid(
                row=r, column=0, sticky="w", pady=4
            )
            ttk.Entry(
                f, textvariable=var, width=14
            ).grid(
                row=r, column=1, sticky="ew", padx=(8, 0), pady=4
            )

        f.columnconfigure(1, weight=1)

        ttk.Separator(f).grid(
            row=4, column=0, columnspan=2, sticky="ew", pady=8
        )

        ttk.Button(
            f,
            text="HACKED ON",
            command=lambda p=panel: p.command_async(
                "HACKED ON",
                p.addr_hacked,
                bool(p.cfg["hacked_on_value"]),
            ),
        ).grid(
            row=5, column=0, columnspan=2, sticky="ew", pady=(4, 4)
        )

        ttk.Button(
            f,
            text="HACKED OFF",
            command=lambda p=panel: p.command_async(
                "HACKED OFF",
                p.addr_hacked,
                bool(p.cfg["hacked_off_value"]),
            ),
        ).grid(
            row=6, column=0, columnspan=2, sticky="ew", pady=4
        )

    def toggle_maintenance(self):
        # If already open, bring it to the foreground.
        if self.maint_window is not None and self.maint_window.winfo_exists():
            self.maint_window.lift()
            self.maint_window.focus_force()
            return

        win = tk.Toplevel(self)
        self.maint_window = win
        win.title("Maintenance")
        win.geometry("680x470")
        win.minsize(620, 430)
        win.transient(self)

        ttk.Label(
            win,
            text="MAINTENANCE",
            font=("Segoe UI", 16, "bold")
        ).pack(pady=(12, 4))

        ttk.Label(
            win,
            text="Diagnostics and test functions",
        ).pack(pady=(0, 4))

        panels = ttk.Frame(win, padding=8)
        panels.pack(fill="both", expand=True)

        self._build_maintenance_panel(panels, self.m262)
        self._build_maintenance_panel(panels, self.delta)

        bottom = ttk.Frame(win, padding=(8, 0, 8, 8))
        bottom.pack(fill="x")

        ttk.Button(
            bottom,
            text="Save configuration",
            command=self.save_all
        ).pack(side="left")

        ttk.Button(
            bottom,
            text="Close",
            command=win.destroy
        ).pack(side="right")

        def on_close():
            try:
                win.destroy()
            finally:
                self.maint_window = None

        win.protocol("WM_DELETE_WINDOW", on_close)

    def synchronize_existing_programs(self):
        """
        Without changing either PLC program:
        1) STOP both PLCs
        2) wait 0.5 s to allow STOP to reset the cycle timers
        3) START M262
        4) wait 10 s
        5) START Delta

        With the current 20-second normal cycle, this leaves
        both traffic lights half a cycle out of phase.
        """
        if not self.m262.connected or not self.delta.connected:
            messagebox.showwarning(
                "Synchronization",
                "Connect both PLCs before synchronizing."
            )
            return

        try:
            addr_m262 = self.m262.parse_addr(self.m262.addr_turn_on)
            addr_delta = self.delta.parse_addr(self.delta.addr_turn_on)
        except Exception:
            messagebox.showwarning(
                "Synchronization",
                "Configure START/STOP for both PLCs."
            )
            return

        def worker():
            try:
                # STOP both PLCs.
                self.m262.node.write_m262_coil(
                    addr_m262, bool(self.m262.cfg["stop_value"])
                )
                self.delta.node.write_coil(
                    addr_delta, bool(self.delta.cfg["stop_value"])
                )

                # Give both emulated PLCs enough time to observe STOP and
                # reset their internal cycle timers before restarting.
                import time
                time.sleep(0.5)

                # START M262 and establish the phase reference.
                self.m262.node.write_m262_coil(
                    addr_m262, bool(self.m262.cfg["start_value"])
                )

                # Visual countdown while the worker thread waits.
                for remaining in range(10, 0, -1):
                    self.after(
                        0,
                        lambda r=remaining: self.sync_status.configure(
                            text=f"SYNCHRONIZING... {r}s"
                        )
                    )
                    time.sleep(1)

                # START Delta after 10 seconds.
                self.delta.node.write_coil(
                    addr_delta, bool(self.delta.cfg["start_value"])
                )

                self.after(
                    0,
                    lambda: self.sync_status.configure(
                        text="SYNCHRONIZED"
                    )
                )
                self.after(
                    4000,
                    lambda: self.sync_status.configure(text="")
                )

            except Exception as exc:
                self.after(
                    0,
                    lambda e=str(exc): messagebox.showerror(
                        "Synchronization", e
                    )
                )
                self.after(
                    0,
                    lambda: self.sync_status.configure(text="")
                )

        threading.Thread(target=worker, daemon=True).start()

    def save_all(self):
        self.cfg["m262"] = self.m262.export_config()
        self.cfg["delta"] = self.delta.export_config()
        save_config(self.cfg)
        messagebox.showinfo(
            "SCADA",
            f"Configuration saved to {CONFIG_FILE.name}",
        )

    def poll_loop(self):
        if not self.running:
            return

        def worker():
            self.m262.poll()
            self.delta.poll()
            self.after(0, self.draw_scene)

        threading.Thread(target=worker, daemon=True).start()

        self.after(
            max(int(self.cfg.get("poll_ms", 500)), 200),
            self.poll_loop,
        )

    @staticmethod
    def draw_lamp(canvas, x, y, radius, active, color):
        canvas.create_oval(
            x-radius,
            y-radius,
            x+radius,
            y+radius,
            fill=(color if active else "#d9d9d9"),
            outline="#222",
            width=3,
        )

    def draw_traffic_light(self, canvas, x, y, title, panel):
        bw, bh = 92, 245

        canvas.create_text(
            x + bw/2,
            y - 20,
            text=title,
            font=("Segoe UI", 12, "bold"),
        )

        canvas.create_rectangle(
            x,
            y,
            x+bw,
            y+bh,
            fill="#202428",
            outline="#111",
            width=2,
        )

        cy = y + 46

        self.draw_lamp(
            canvas, x+bw/2, cy, 27, panel.red_on, "#ff2a2a"
        )
        self.draw_lamp(
            canvas, x+bw/2, cy+73, 27, panel.yellow_on, "#ffd52a"
        )
        self.draw_lamp(
            canvas, x+bw/2, cy+146, 27, panel.green_on, "#28d75f"
        )


    def draw_scene(self):
        if not hasattr(self, "canvas"):
            return

        c = self.canvas
        c.delete("all")

        w = max(c.winfo_width(), 950)
        h = max(c.winfo_height(), 650)

        road = "#55585c"

        # Roads.
        c.create_rectangle(
            0, h*0.36, w, h*0.64,
            fill=road, outline=""
        )
        c.create_rectangle(
            w*0.37, 0, w*0.63, h,
            fill=road, outline=""
        )

        # Center lines.
        c.create_line(
            0, h/2, w*0.37, h/2,
            fill="white", width=2, dash=(10, 10)
        )
        c.create_line(
            w*0.63, h/2, w, h/2,
            fill="white", width=2, dash=(10, 10)
        )
        c.create_line(
            w/2, 0, w/2, h*0.36,
            fill="white", width=2, dash=(10, 10)
        )
        c.create_line(
            w/2, h*0.64, w/2, h,
            fill="white", width=2, dash=(10, 10)
        )

        # M262 controls North/South.
        # Traffic lights positioned close to the intersection corners.
        self.draw_traffic_light(
            c,
            w*0.625,
            h*0.10,
            "",
            self.m262,
        )

        # Move only the label slightly to the right.
        c.create_text(
            w*0.735,
            h*0.22,
            anchor="w",
            text="M262 · STREET A",
            font=("Segoe UI", 12, "bold"),
        )

        # Delta controls East/West. Place it near the lower-left corner
        # with its label in the clear area.
        self.draw_traffic_light(
            c,
            w*0.31,
            h*0.55,
            "",
            self.delta,
        )

        c.create_text(
            w*0.50,
            24,
            text="STREET A · NORTH / SOUTH",
            font=("Segoe UI", 12, "bold"),
        )

        c.create_text(
            18,
            h*0.43,
            anchor="w",
            text="STREET B · EAST / WEST",
            font=("Segoe UI", 12, "bold"),
        )

        c.create_text(
            w*0.23,
            h*0.69,
            anchor="center",
            text="DELTA · STREET B",
            font=("Segoe UI", 12, "bold"),
        )

        # General status.
        c.create_rectangle(
            20, 20, 350, 125,
            fill="#f2f2f2",
            outline="#333",
        )

        c.create_text(
            38, 45,
            anchor="w",
            text="GENERAL STATUS",
            font=("Segoe UI", 13, "bold"),
        )

        c.create_text(
            38, 76,
            anchor="w",
            text=f"M262: {'ONLINE' if self.m262.connected else 'OFFLINE'}",
            font=("Segoe UI", 11),
        )

        c.create_text(
            38, 103,
            anchor="w",
            text=f"Delta: {'ONLINE' if self.delta.connected else 'OFFLINE'}",
            font=("Segoe UI", 11),
        )

    def on_close(self):
        self.running = False
        self.m262.node.close()
        self.delta.node.close()
        self.destroy()


if __name__ == "__main__":
    App().mainloop()
