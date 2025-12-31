import pathlib
import libximc.highlevel as ximc
import os, sys
import pyvisa
import time
import numpy as np
import uproot
import argparse
import awkward as ak
import utils.artwork as artwork
import matplotlib.pyplot as plt
import mplhep as hep
import pyvisa
import struct
import re

def xyz_scan(x_axis, y_axis, z_axis, x_start, x_end, y_start, y_end, z_start, z_end, step_size, scope):
    peak_array = np.zeros((int((x_end - x_start) / step_size) + 1, int((y_end - y_start) / step_size) + 1,
                           int((z_end - z_start) / step_size) + 1))
    charge_array = np.zeros((int((x_end - x_start) / step_size) + 1, int((y_end - y_start) / step_size) + 1,
                             int((z_end - z_start) / step_size) + 1))
    for z in range(z_start, z_end + 1, step_size):
        z_axis.command_move(z, 0)
        z_axis.command_wait_for_stop(10)
        for y in range(y_start, y_end + 1, step_size):
            y_axis.command_move(y, 0)
            y_axis.command_wait_for_stop(10)
            for x in range(x_start, x_end + 1, step_size):
                x_axis.command_move(-x, 0)
                x_axis.command_wait_for_stop(10)

                peak, charge = 0, 0
                for i in range(10):
                    peak_try, charge_try = scope.scan()  # Get the peak value from the oscilloscope
                    peak += peak_try
                    charge += charge_try
                peak /= 10
                charge /= 10

                ### pulse peak measurement###
                peak_array[int((z - z_start) / step_size), int((y - y_start) / step_size),
                           int((x - x_start) / step_size)] = peak
                charge_array[int((z - z_start) / step_size), int((y - y_start) / step_size),
                             int((x - x_start) / step_size)] = charge
                #############################
                print(f"Current position: X: {x_axis.get_position().Position}, Y: {y_axis.get_position().Position}, Z: {z_axis.get_position().Position}, pulse peak: {peak}, charge: {charge}")
    # Move back to the starting position
    time.sleep(1)  # Wait for the motors to stop
    x_axis.command_move(0, 0)
    y_axis.command_move(0, 0)
    z_axis.command_move(0, 0)
    x_axis.command_wait_for_stop(100)
    y_axis.command_wait_for_stop(100)
    z_axis.command_wait_for_stop(100)
    np.save('xyz_peak.npy', peak_array)
    np.save('xyz_charge.npy', charge_array)


def xy_scan(x_axis, y_axis, x_start, x_end, y_start, y_end, step_size, scope):
    # x plus -> plate move to the right side
    # y plus -> plate move to the down side
    # z plus -> plate move down (to the sample)
    # make a 2d array of positions
    peak_array = np.zeros((int((x_end - x_start) / step_size) + 1, int((y_end - y_start) / step_size) + 1))
    charge_array = np.zeros((int((x_end - x_start) / step_size) + 1, int((y_end - y_start) / step_size) + 1))
    for y in range(y_start, y_end + 1, step_size):
        y_axis.command_move(y, 0)
        y_axis.command_wait_for_stop(10)
        for x in range(x_start, x_end + 1, step_size):
            x_axis.command_move(-x, 0)
            x_axis.command_wait_for_stop(10)

            peak, charge = 0, 0
            for i in range(10):
                peak_try, charge_try = scope.scan()  # Get the peak value from the oscilloscope
                #print(peak_try, charge_try)
                peak += peak_try
                charge += charge_try
            peak /= 10
            charge /= 10

            ### pulse peak measurement###
            peak_array[int((y - y_start) / step_size),int((x - x_start) / step_size)] = peak
            charge_array[int((y - y_start) / step_size),int((x - x_start) / step_size)] = charge
            #print(array)
            #############################
            print(f"Current position: X: {x_axis.get_position().Position}, Y: {y_axis.get_position().Position}, pulse peak: {peak}, charge: {charge}")
    # Move back to the starting position
    time.sleep(1)  # Wait for the motors to stop
    x_axis.command_move(0, 0)
    y_axis.command_move(0, 0)
    x_axis.command_wait_for_stop(100)
    y_axis.command_wait_for_stop(100)

    np.save('xy_peak.npy', peak_array)
    np.save('xy_charge.npy', charge_array)

    plt.imshow((peak_array), cmap='hot', interpolation='nearest')
    plt.colorbar()
    plt.title("Pulse Peak Heatmap")
    plt.xlabel("X Axis")
    plt.ylabel("Y Axis")
    plt.savefig('xy_peak.png')
    plt.clf()

    plt.imshow((charge_array), cmap='hot', interpolation='nearest')
    plt.colorbar()
    plt.title("Pulse Charge Heatmap")
    plt.xlabel("X Axis")
    plt.ylabel("Y Axis")
    plt.savefig('xy_charge.png')
    plt.clf()



def __version__():
    return 'v0.8'

def __developer__():
    return 'Taiwoo Kim and Jongyeob Kim'

def __target__():
    return 'Tektronix Series Oscilloscope'

def dqmDraw(channel, x, y):
    plt.style.use(hep.style.ROOT)
    plt.figure(figsize=(10, 6))
    hep.cms.label(llabel='KNU DQM', rlabel='')
    if channel == 1:
        color = 'red'
    elif channel == 2:
        color = 'blue'
    elif channel == 3:
        color = 'purple'
    elif channel == 4:
        color = 'green'
    else:
        raise ValueError('Invalid channel number')
    x = x * 1e9
    #print(x)
    plt.plot(x, y, color=color)
    #plt.xlim(-50,50)
    plt.xlabel('Time (ns)')
    plt.ylabel('Voltage (V)')
    plt.savefig(f'waveform_ch{channel}.png')
    plt.close()

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

    def scan(self):
        self.runtheScope()
        data = {}
        ch = 1
        x, y = self.readChannel(ch)
        #data[f'ch{ch}'] = ak.Array([y])
        # calculating pedestal mean and rms
        pedestal_mean = np.mean(y[:400])
        pedestal_total = pedestal_mean * len(y)
        collected_charge = ((np.sum(y) * (x[1] - x[0])) - (pedestal_total * (x[1] - x[0]))) * 1e15 / 50 # in fC
        #print('Collected charge:', collected_charge, 'fC')
        #print(len(y))
        window_size = 400
        peak_voltage = abs(np.min(y[1200:int(1200   + window_size)]) - pedestal_mean)
        return peak_voltage, collected_charge

#####################################################################################################################3

# Start time
start_time = time.time()

# default settings
resource_name = 'TCPIP::192.168.100.100::INSTR' ## 내부망 IP 주소 (사전 정의됨. 바꾸지 마시오.)

if __name__ == '__main__':
    scope = Lecroy(resource_name)

    # Device URI 설정
    device_uri1 = "xi-com:/dev/ttyACM0"
    device_uri3 = "xi-com:/dev/ttyACM1"
    device_uri2 = "xi-com:/dev/ttyACM2"

    # Axis 객체 생성
    z_axis = ximc.Axis(device_uri1)
    x_axis = ximc.Axis(device_uri3)
    y_axis = ximc.Axis(device_uri2)

    # Device 열기 (→ patched_open 으로 low-level open_device 호출됨)
    z_axis.open_device()
    x_axis.open_device()
    y_axis.open_device()

    # 위치 0으로 설정
    x_axis.command_zero()
    y_axis.command_zero()
    z_axis.command_zero()

    # XY 스캔 실행
    xy_scan(x_axis, y_axis, -40, 40, -40, 40, 4, scope)
    #xyz_scan(x_axis, y_axis, z_axis, -40, 40, -40, 40, -40, 40, 2, scope)

    # Device 닫기
    x_axis.close_device()
    y_axis.close_device()
    z_axis.close_device()

    # End time
    print('File saved on "output/" directory')
    end_time = time.time()
    print(f'Elapsed time: {end_time - start_time:.2f} sec')

    exit()
#####################################################################################################################