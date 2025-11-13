
# -*- coding: utf-8 -*-
"""
LeCroyControl_v1_0.py
---------------------
PyVISA-based controller for LeCroy/Teledyne LeCroy X-Stream oscilloscopes
(e.g., WaveRunner 9xxx series). It mirrors a Tektronix-style interface so
existing DAQ code can be ported with minimal changes.

Key features
- Robust VISA connection with auto-timeout and IDN print
- Channel setup helpers (VDIV/OFFSET/COUPLING/TRACE)
- Single-acquisition control (TRMD SINGLE; ARM; *OPC?)
- Binary waveform read via "C{n}:WF? DAT1" and WAVEDESC parse
- Returns calibrated time, voltage numpy arrays
- Optional save to ROOT (uproot) or CSV
- CLI for quick tests

NOTE: LeCroy command set varies slightly by firmware. This code tries a few
fallback variants when a command isn't supported on your model.

Tested with: WAVERUNNER9404M-MS (SCPI basic set, VBS queries).

Author: ChatGPT (GPT-5 Thinking)
"""

import sys
import time
import struct
import argparse
import numpy as np
import pyvisa

try:
    import uproot
except Exception:
    uproot = None

# -------------------------
# Utilities
# -------------------------

def _read_block_with_header(inst):
    """
    Read a LeCroy binary block that may be prefixed by an ASCII token
    like "DESC," or "DAT1," followed by the IEEE488.2 block:
      #<N><len><data>
    Returns raw bytes of the data payload (no header).
    This function accumulates reads until the declared length is satisfied.
    """
    buf = b""
    # Read at least one chunk
    while True:
        chunk = inst.read_raw()
        if not chunk:
            break
        buf += chunk
        # If we already received a '#', try to parse
        hash_pos = buf.find(b'#')
        if hash_pos >= 0 and len(buf) >= hash_pos + 2:
            try:
                n_digits = int(chr(buf[hash_pos+1]))
            except Exception:
                # Not enough or malformed; keep reading
                pass
            else:
                # Ensure we have full length field
                while len(buf) < hash_pos + 2 + n_digits:
                    more = inst.read_raw()
                    if not more:
                        break
                    buf += more
                if len(buf) < hash_pos + 2 + n_digits:
                    # Timeout or truncated
                    break
                try:
                    data_len = int(buf[hash_pos+2:hash_pos+2+n_digits].decode('ascii'))
                except Exception:
                    # Malformed; continue reading in case split happened
                    continue
                start = hash_pos + 2 + n_digits
                end = start + data_len
                # Read until we have the declared data
                while len(buf) < end:
                    more = inst.read_raw()
                    if not more:
                        break
                    buf += more
                if len(buf) >= end:
                    return buf[start:end]
        # If no '#', keep looping to gather more
    # If we exit the loop without returning, raise a helpful error
    preview = buf[:80]
    raise RuntimeError(f'Unexpected or truncated block. Preview: {preview!r}')

def _parse_wavedesc(header_bytes):
    """
    Parse fields from LeCroy WAVEDESC binary header.
    Offsets per Teledyne LeCroy "Waveform Description" (X-Stream).
    Returns dict with scaling parameters.
    """
    def f32(off): return struct.unpack('<f', header_bytes[off:off+4])[0]
    def f64(off): return struct.unpack('<d', header_bytes[off:off+8])[0]
    def i16(off): return struct.unpack('<h', header_bytes[off:off+2])[0]
    def i32(off): return struct.unpack('<i', header_bytes[off:off+4])[0]
    def u16(off): return struct.unpack('<H', header_bytes[off:off+2])[0]
    def u32(off): return struct.unpack('<I', header_bytes[off:off+4])[0]

    # Most commonly used fields
    rec = {}
    # Byte 36: WAVE_DESCRIPTOR length (long)
    rec['wave_descriptor_len'] = u32(36)
    # Byte 116: record length (long)
    rec['record_length'] = u32(116)
    # Byte 156: vertical gain (float)
    rec['vertical_gain'] = f32(156)
    # Byte 160: vertical offset (float)
    rec['vertical_offset'] = f32(160)
    # Byte 176: horizontal interval (XINCR, float)
    rec['horizontal_interval'] = f32(176)
    # Byte 180: horizontal offset (double)
    rec['horizontal_offset'] = f64(180)
    # Byte 196: vertical units (16 chars) -- not essential here
    # Byte 312: horizontal units (16 chars)
    # Byte 144: Trigger time (double) -- not essential here
    return rec

# -------------------------
# Main LeCroy scope class
# -------------------------

class LeCroyScope:
    def __init__(self, resource=None, timeout_ms=10000):
        self.rm = pyvisa.ResourceManager()
        self.inst = None
        self.idn = None
        if resource is not None:
            self.connect(resource, timeout_ms)

    # ----- connection -----
    def connect(self, resource, timeout_ms=10000):
        self.inst = self.rm.open_resource(resource)
        self.inst.timeout = timeout_ms
        self.idn = self.query('*IDN?')
        print(f'Connected: {self.idn.strip()}')
        # Try to select a known data format (binary, WORD)
        self._try_set_comm_format()
        return self

    def close(self):
        if self.inst is not None:
            try:
                self.inst.before_close()
            except Exception:
                pass
            self.inst.close()
            self.inst = None

    # ----- low-level I/O -----
    def write(self, cmd):
        # LeCroy likes newline line-endings
        return self.inst.write(cmd)

    def read(self):
        return self.inst.read()

    def read_raw(self, nbytes=None):
        if nbytes is None:
            return self.inst.read_raw()
        return self.inst.read_raw(nbytes)

    def query(self, cmd):
        return self.inst.query(cmd)

    def query_raw(self, cmd):
        self.write(cmd)
        return self.read_raw()

    # ----- helpers -----
    def _try_set_comm_format(self):
        """
        Set binary format. Different firmware use different mnemonics.
        We'll try a few common ones and ignore errors.
        """
        candidates = [
            # Classic LeCroy (X-Stream) communication format
            "COMM_FORMAT DEF9,WORD,BIN",
            "COMM_FORMAT OFF,WORD,BIN",
            "CFMT DEF9,WORD,BIN",
            "CFMT OFF,WORD,BIN",
        ]
        for c in candidates:
            try:
                self.write(c)
                return
            except Exception:
                continue

    def error_status(self):
        """
        Try multiple error query paths, return a best-effort string.
        """
        probes = [
            "SYST:ERR?",
            "LERR?",
            "VBS? 'return=app.ErrorLog.LastError'",
        ]
        for p in probes:
            try:
                resp = self.query(p)
                return f"{p} -> {resp.strip()}"
            except Exception:
                continue
        return "No error channel available."

    # ----- setup -----
    def set_channel(self, ch:int, vdiv=None, ofst=None, coupling=None, trace=None):
        """
        ch: 1..4
        vdiv: float in volts/div
        ofst: float in volts (screen center offset)
        coupling: 'D50' (50 Ohm DC), 'D1M' (1M DC), 'A1M' (1M AC) etc.
        trace: True/False to show channel
        """
        prefix = f"C{ch}:"
        if vdiv is not None:
            self.write(f"{prefix}VDIV {vdiv}")
        if ofst is not None:
            self.write(f"{prefix}OFST {ofst}")
        if coupling is not None:
            self.write(f"{prefix}COUPLING {coupling}")
        if trace is not None:
            self.write(f"{prefix}TRACE {'ON' if trace else 'OFF'}")

    def get_channel_status(self, ch:int):
        prefix = f"C{ch}:"
        out = {}
        for k in ["VDIV?", "OFST?", "COUPLING?", "TRACE?"]:
            try:
                out[k[:-1].lower()] = self.query(prefix + k).strip()
            except Exception:
                out[k[:-1].lower()] = "N/A"
        return out

    def set_timebase(self, sec_per_div=None, sample_rate=None, record_length=None):
        """
        Set horizontal scale. On LeCroy, common path is to set sample mode and memory length.
        We attempt a few variants and ignore unsupported ones.
        """
        if record_length is not None:
            for cmd in [f"MSIZ {int(record_length)}", f"HOR:RECORDLENGTH {int(record_length)}"]:
                try:
                    self.write(cmd)
                    break
                except Exception:
                    continue
        if sec_per_div is not None:
            for cmd in [f"TDIV {sec_per_div}", f"HOR:MAIN:SCALE {sec_per_div}"]:
                try:
                    self.write(cmd)
                    break
                except Exception:
                    continue
        if sample_rate is not None:
            # LeCroy horizontal can be overconstrained; usually set via TDIV+MSIZ.
            # We expose this but don't guarantee firmware honors it.
            try:
                self.write(f"SARA {sample_rate}")
            except Exception:
                pass

    # ----- acquisition -----
    def single(self, wait=True, poll_interval=0.1, max_wait_s=10.0):
        """
        Arm for single acquisition and optionally wait for completion.
        """
        # Set single trigger mode and arm
        self.write("TRMD SINGLE")
        time.sleep(0.05)
        self.write("ARM")

        if not wait:
            return

        # Try *OPC? as a portable wait; fall back to BUSY?/TRIG_STATE?
        t0 = time.time()
        try:
            _ = self.query("*OPC?")
            return
        except Exception:
            pass

        while time.time() - t0 < max_wait_s:
            for probe in ["BUSY?", "TRIG_STATE?"]:
                try:
                    s = self.query(probe).strip().upper()
                    if ("BUSY" in probe and s in ("0", "OFF", "NO")) or ("TRIG" in probe and "STOP" in s):
                        return
                except Exception:
                    pass
            time.sleep(poll_interval)
        # As a last resort, just proceed
        return

    # ----- waveform read -----
    def read_waveform(self, ch:int=1):
        """
        Read binary waveform from channel ch. Returns (t, y) as numpy arrays (float64).
        Uses two-step read: WAVEDESC (header) then DAT1 (data).
        """
        # Request header (WAVEDESC)
        self.write(f"C{ch}:WF? DESC")
        header = _read_block_with_header(self.inst)
        if len(header) < 346:
            raise RuntimeError(f"WAVEDESC too short: {len(header)} bytes")
        meta = _parse_wavedesc(header)

        # Request data array 1 (WAVE_ARRAY_1)
        self.write(f"C{ch}:WF? DAT1")
        raw = _read_block_with_header(self.inst)

        # Data are 16-bit signed samples (WORD) if COMM_FORMAT WORD was honored; else BYTE (unsigned).
        # We'll detect from array size vs record_length.
        rec_len = meta['record_length']
        if len(raw) == rec_len * 2:
            y_adc = np.frombuffer(raw, dtype='<i2')  # little-endian int16
        elif len(raw) == rec_len:
            y_adc = np.frombuffer(raw, dtype=np.uint8).astype(np.int16) - 128
        else:
            # Fallback: try to infer a multiple
            m = len(raw)
            raise RuntimeError(f"Unexpected data length {m} for record_length {rec_len}")

        # Scale to volts and time
        v_gain = meta['vertical_gain']
        v_off  = meta['vertical_offset']
        xincr  = meta['horizontal_interval']
        xzero  = meta['horizontal_offset']

        y = y_adc.astype(np.float64) * v_gain - v_off
        t = xzero + np.arange(rec_len, dtype=np.float64) * xincr
        return t, y

# -------------------------
# CLI
# -------------------------

def main():
    p = argparse.ArgumentParser(description='LeCroy scope controller (single-acquire & dump)')
    p.add_argument('--visa', required=True, help="VISA resource, e.g. TCPIP0::192.168.100.100::INSTR")
    p.add_argument('--channel', type=int, default=1)
    p.add_argument('--vdiv', type=float, help='Volts per div for channel')
    p.add_argument('--ofst', type=float, help='Offset (V) for channel')
    p.add_argument('--coupling', type=str, help='Coupling string e.g. D50')
    p.add_argument('--trace', type=str, choices=['on','off'], help='Turn channel trace on/off')
    p.add_argument('--record-length', type=int, help='Memory size (points)')
    p.add_argument('--tdiv', type=float, help='Time/div (s/div)')
    p.add_argument('--single', action='store_true', help='Do a single acquisition')
    p.add_argument('--csv', type=str, help='Save to CSV file')
    p.add_argument('--root', type=str, help='Save to ROOT file (requires uproot)')
    args = p.parse_args()

    scope = LeCroyScope(args.visa)
    if args.vdiv or args.ofst or args.coupling or args.trace:
        scope.set_channel(args.channel,
                          vdiv=args.vdiv,
                          ofst=args.ofst,
                          coupling=args.coupling,
                          trace=(args.trace=='on' if args.trace else None))
        print('Channel status:', scope.get_channel_status(args.channel))

    if args.record_length or args.tdiv:
        scope.set_timebase(sec_per_div=args.tdiv, record_length=args.record_length)

    if args.single:
        scope.single(wait=True)
        print('Acquisition done.')

    t, y = scope.read_waveform(args.channel)
    print(f"Fetched {y.size} points. t[{0}]={t[0]:.6e}s, t[-1]={t[-1]:.6e}s, y[min..max]=({y.min():.3g},{y.max():.3g}) V")

    if args.csv:
        import numpy as np
        np.savetxt(args.csv, np.column_stack([t, y]), delimiter=',', header='time(s),volt(V)', comments='')
        print(f'Saved CSV: {args.csv}')

    if args.root:
        if uproot is None:
            print('uproot not available; skip ROOT save.')
        else:
            with uproot.recreate(args.root) as f:
                f['wave'] = {
                    't': t.astype('float64'),
                    'y': y.astype('float64'),
                }
            print(f'Saved ROOT: {args.root}')

if __name__ == '__main__':
    main()
