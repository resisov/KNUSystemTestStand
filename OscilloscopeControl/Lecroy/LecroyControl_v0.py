# -*- coding: utf-8 -*-
import os, sys
import re
from tqdm import tqdm
import pyvisa
import time
import numpy as np
import uproot
import argparse
import awkward as ak
import utils.artwork as artwork
from utils.Keithley2470 import Keithley
import matplotlib.pyplot as plt
import mplhep as hep
from scipy.optimize import curve_fit
import subprocess
import struct
import numpy as np

def __version__():
    return 'v0.1'

def __developer__():
    return 'Taiwoo Kim'

def __target__():
    return 'Lecroy Series Oscilloscope'

def sigmoid(x, a, b, c):
    """Sigmoid function for curve fitting."""
    return c / (1 + np.exp(-a * (x - b)))

def gaussian(x, amp, mean, sigma):
    """Gaussian function for curve fitting."""
    return -(amp * np.exp(-((x - mean) ** 2) / (2 * sigma ** 2)))
def pos_gaussian(x, amp, mean, sigma):
    """Gaussian function for curve fitting."""
    return amp * np.exp(-((x - mean) ** 2) / (2 * sigma ** 2))

class Lecroy:
    def __init__(self, resource_name):
        self.rm = pyvisa.ResourceManager()
        try:
            self.inst = self.rm.open_resource(resource_name)
            self.inst.timeout = 10000
            self.idn = self.inst.query("*IDN?")
            print(f"Connected to: {self.idn.strip()}")
        
        except:
            print("Error: Could not connect to the oscilloscope.")
            sys.exit(1)

    def _extract(self, setup_str, key):
        """
        Extracts values from WAVEFORM_SETUP response.
        Example entry: "HORIZ_INTERVAL,1.0000E-10"
        """
        pattern = key + r",([\-\d\.Ee+]+)"
        match = re.search(pattern, setup_str)
        if not match:
            raise ValueError(f"Cannot find {key} in WAVEFORM_SETUP")
        return match.group(1)

    def _parse_wavedesc(self, ch):
        """
        ch = 'C1', 'C2' ...
        C1:WF? DESC 로 받아온 descriptor 안에서
        HORIZ_INTERVAL, HORIZ_OFFSET, VERTICAL_GAIN, VERTICAL_OFFSET 만 뽑는다.
        """
        # descriptor 요청
        self.inst.write(f"{ch}:WF? DESC")
        desc_raw = self.inst.read_raw()

        # 'WAVEDESC' 시작 위치 찾기
        wd_offset = desc_raw.find(b'WAVEDESC')
        if wd_offset == -1:
            raise RuntimeError("WAVEDESC not found in descriptor from scope")

        # COMM_ORDER (byte at wd_offset+34): 0 = high-first('>'), 1 = low-first('<')
        comm_order = struct.unpack_from('?', desc_raw, wd_offset + 34)[0]
        endi = '<' if comm_order else '>'  # little / big endian

        # 필요한 몇 개만 읽어옴 (LECROY_2_3 템플릿 기준 오프셋)
        vert_gain      = struct.unpack_from(endi + 'f', desc_raw, wd_offset + 156)[0]
        vert_offset    = struct.unpack_from(endi + 'f', desc_raw, wd_offset + 160)[0]
        horiz_interval = struct.unpack_from(endi + 'f', desc_raw, wd_offset + 176)[0]
        horiz_offset   = struct.unpack_from(endi + 'd', desc_raw, wd_offset + 180)[0]

        return horiz_interval, horiz_offset, vert_gain, vert_offset, endi

    def setHorizontalWindow(self, window):
        # window = seconds per division
        self.inst.write(f'TIME_DIV {window}')

    def setTrigger(self, channel, level):
        # 채널 EXT 고정
        self.inst.write(f"EX:TRIG_LEVEL {level}V")

    def runtheScope(self):
        # 1. 싱글 트리거 모드로 설정
        self.inst.write("TRIG_MODE SINGLE")

        # 2. 한 번 acquisition ARM 하고, 끝날 때까지 WAIT
        #    WAIT 은 acquisition 끝날 때까지 다음 명령 처리를 막아줌
        self.inst.write("ARM;WAIT")

        # 3. (선택) 동기 확인용 – Tek 의 *OPC? 와 비슷하게 사용
        self.inst.query("*OPC?")

    def readChannel(self, channel):
        """
        LeCroy WaveRunner: C{channel} 의 파형을 읽어서
        x_data (time [s]), y_data (voltage [V]) 를 반환.
        """
        ch = f"C{channel}"

        # 데이터 포맷: DEF9, WORD, BIN (16bit, binary)
        self.inst.write("COMM_FORMAT DEF9,WORD,BIN")

        # WAVEDESC 에서 스케일 정보 파싱
        x_inc, x_off, y_gain, y_off, endi = self._parse_wavedesc(ch)

        # 실제 파형 데이터 요청
        self.inst.write(f"{ch}:WF? DAT1")
        raw = self.inst.read_raw()

        # IEEE 488.2 definite-length block 파싱: "#9<ndigits><nbytes><data...>"
        hash_index = raw.find(b'#')
        if hash_index == -1:
            raise RuntimeError("No IEEE488.2 block header ('#') in waveform data")

        ndigits = int(chr(raw[hash_index + 1]))
        nbytes = int(raw[hash_index + 2: hash_index + 2 + ndigits])
        data_start = hash_index + 2 + ndigits
        data_end = data_start + nbytes

        data = raw[data_start:data_end]

        # endi 정보에 맞춰 16bit signed 읽기
        dtype = np.dtype(endi + 'i2')    # '>' or '<' + int16
        y_raw = np.frombuffer(data, dtype=dtype)

        # 세로축: value = VERTICAL_GAIN * raw - VERTICAL_OFFSET
        y_data = y_gain * y_raw - y_off

        # 가로축: x[i] = HORIZ_INTERVAL * i + HORIZ_OFFSET
        x_data = x_off + np.arange(len(y_data)) * x_inc

        if len(y_data) == 0:
            raise RuntimeError(f"Empty waveform from {ch} (len(y_data)=0). "
                               "Check trigger settings / acquisition mode.")

        return x_data, y_data

    
    def acquisition(self, nEvents):
        print(f'Horizontal window: {horizontalwindow} sec',
            f'Trigger channel: {trigger_channel}',
            f'Trigger level: {trigger_level} V')
        # 1) 획득 정지 (Run/Stop 버튼의 STOP에 해당)
        self.inst.write("TRMD STOP")   # TRMD {SINGLE, AUTO, NORM, STOP}
        self.inst.write("COMM_FORMAT DEF9,WORD,BIN")
        self.inst.write(f"TIME_DIV {horizontalwindow}")

        print('Acquiring waveforms...')

        intermediate_idx = 0
        tempdir = 'temp/'
        batch_files = []

        for i in tqdm(range(nEvents), desc='Acquiring', unit='event'):
            self.runtheScope()   # LeCroy용 runtheScope (TRIG_MODE SINGLE; ARM;WAIT) 버전 사용

            data = {}
            for ch in range(1, 2):
                x, y = self.readChannel(ch)
                if ch == 1:
                    data['time'] = ak.Array([x])
                data[f'ch{ch}'] = ak.Array([y])

                # --- 이하 Tek 버전과 동일 ---
                peak_index = np.argmax(np.abs(y))
                peak_value = y[peak_index]
                peak_time = x[peak_index]
                peak_voltage = np.max(np.abs(y))

                data[f'ch{ch}_peak_volt'] = ak.Array([peak_voltage])
                data[f'ch{ch}_peak_time'] = ak.Array([peak_time])
                data[f'ch{ch}_peak_index'] = ak.Array([peak_index])

                integral = np.sum(y[peak_index - 100:peak_index + 100]) * (x[1] - x[0])

                pedestal_total = np.sum(y[:400]) / 400 * 200
                pedestal_mean = np.mean(y[:400])
                pedestal_rms = np.std(y[:400])
                data[f'ch{ch}_ped_total'] = ak.Array([pedestal_total])
                data[f'ch{ch}_ped_mean'] = ak.Array([pedestal_mean])
                data[f'ch{ch}_ped_rms'] = ak.Array([pedestal_rms])

                collected_charge = (integral - (pedestal_total * (x[1] - x[0]))) * 1e15 / 50
                data[f'ch{ch}_collected_charge'] = ak.Array([collected_charge])

                if peak_voltage *1e3 < 0.6:
                    data[f'ch{ch}_toa'] = ak.Array([-99.0])
                    print(f'Event {i+1}/{nEvents} Channel {ch}: Peak Voltage = {peak_voltage*1e3:.3f} mV, Peak Time = {peak_time*1e9:.3f} ns, toa = {data[f"ch{ch}_toa"][0]*1e9:.3f} ns')
                    continue
                try:
                    fit_x = x[peak_index - 100:peak_index + 100]
                    fit_y = y[peak_index - 100:peak_index + 100]
                    popt, _ = curve_fit(gaussian, fit_x, fit_y,
                                        p0=[peak_voltage, peak_time, 1e-9],
                                        maxfev=10000)
                    fit_amp, fit_mean, fit_sigma = popt
                    fit_curve = gaussian(x, fit_amp, fit_mean, fit_sigma)
                    toa_time = fit_mean - (1.794 * fit_sigma)
                    data[f'ch{ch}_toa'] = ak.Array([toa_time])
                except:
                    data[f'ch{ch}_toa'] = ak.Array([-99.0])
                print(f'Event {i+1}/{nEvents} Channel {ch}: Peak Voltage = {peak_voltage*1e3:.3f} mV, Peak Time = {peak_time*1e9:.3f} ns, toa = {data[f"ch{ch}_toa"][0]*1e9:.3f} ns')

            out_file = f'{tempdir}waveforms_temp_{i}.root'
            batch_files.append(out_file)
            with uproot.recreate(out_file) as f:
                f['Events'] = {k: ak.Array(v) for k, v in data.items()}

            if (i + 1) % 1000 == 0 or (i + 1) == nEvents:
                intermediate_file = f'{tempdir}intermediate_{intermediate_idx}.root'
                print(f'Merging {len(batch_files)} files into {intermediate_file}...')
                os.system(f"hadd -f {intermediate_file} " + ' '.join(batch_files))
                for f in batch_files:
                    os.remove(f)
                batch_files = []
                intermediate_idx += 1

    def mergingROOT(self):
        tempdir = 'temp/'
        outdir = args.output_dir
        outname = args.output
        intermediate_files = sorted([os.path.join(tempdir, f) for f in os.listdir(tempdir) if f.startswith('intermediate_')])
        if len(intermediate_files) == 0:
            print('No intermediate files found!')
            return
        cmd = f"hadd -f {outdir}{outname} " + ' '.join(intermediate_files)
        print(f'Final merge: {cmd}')
        os.system(cmd)
        for f in intermediate_files:
            os.remove(f)


parser = argparse.ArgumentParser(description='Oscilloscope control')
parser.add_argument('--nEvents', type=int, default=10, help='Number of events to acquire')
parser.add_argument('--horizontalwindow', type=float, default=5e-9, help='Horizontal window')
parser.add_argument('--trigger_channel', type=int, default=2, help='Trigger channel')
parser.add_argument('--trigger_level', type=float, default=-0.4000, help='Trigger level')
parser.add_argument('--output_dir', type=str, default='/home/knutimingdaq01/Desktop/KNUSystemTestStand/OscilloscopeControl/output/', help='Output directory')
parser.add_argument('--output', type=str, default='waveforms_merged.root', help='Output name')
parser.add_argument('--scan', type=str, default='False', help='Scan mode (True/False)')
parser.add_argument('--scan_start', type=float, default=-140, help='Scan start value')
parser.add_argument('--scan_stop', type=float, default=-140, help='Scan stop value')
args = parser.parse_args()

# Start time
start_time = time.time()

# default settings
resource_name = 'TCPIP::192.168.100.100::INSTR'
horizontalwindow = args.horizontalwindow
trigger_channel = args.trigger_channel
trigger_level = args.trigger_level

if __name__ == '__main__':
    print(f'Version: {__version__()}')
    print(f'Developer: {__developer__()}')
    print(f'Target: {__target__()}')
    print('')
    ## output directory check
    if not os.path.exists(args.output_dir):
        os.makedirs(args.output_dir)
    if args.scan == 'False':
        scope = Lecroy(resource_name)
        scope.setHorizontalWindow(horizontalwindow)
        scope.setTrigger('EXT',trigger_level)
        scope.acquisition(args.nEvents)
        scope.mergingROOT()
    else:
        keithley = Keithley()
        keithley.reset_voltage()  # Reset the voltage to 0V before starting the scan
        keithley.apply_voltage(args.scan_start)  # Apply the starting voltage
        for i in tqdm(np.arange(args.scan_start, args.scan_stop-1, -10), desc='Scanning', unit='step'):
            print(f'Scanning: {i} V')
            # Adjust the voltage for each step
            scope = Lecroy(resource_name)
            scope.setHorizontalWindow(horizontalwindow)
            scope.setTrigger('EXT',trigger_level)
            scope.acquisition(args.nEvents)
            scope.mergingROOT()
            ## Save the output file with the scan value
            output_file = f'{args.output_dir}waveforms_scan_{int(abs(i))}.root'
            os.rename(f'{args.output_dir}{args.output}', output_file)
            keithley.adjust_voltage(-10)
            time.sleep(0.5)
        # Reset the voltage to 0V after the scan
        print('Scan completed. Resetting voltage to 0V.')
        keithley.reset_voltage()  # Reset the voltage to 0V after the scan