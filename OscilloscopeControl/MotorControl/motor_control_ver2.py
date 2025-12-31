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

def xyz_scan(x_axis, y_axis, z_axis, x_start, x_end, y_start, y_end, z_start, z_end, step_size, scope):
    peak_array = np.zeros((int((x_end - x_start) / step_size) + 1, int((y_end - y_start) / step_size) + 1, int((z_end - z_start) / step_size) + 1))
    charge_array = np.zeros((int((x_end - x_start) / step_size) + 1, int((y_end - y_start) / step_size) + 1, int((z_end - z_start) / step_size) + 1))
    for z in range(z_start, z_end + 1, step_size):
        z_axis.command_move(-z, 0)
        z_axis.command_wait_for_stop(10)
        for y in range(y_start, y_end + 1, step_size):
            y_axis.command_move(y, 0)
            y_axis.command_wait_for_stop(10)
            for x in range(x_start, x_end + 1, step_size):
                x_axis.command_move(-x, 0)
                x_axis.command_wait_for_stop(10)

                peak, charge = 0, 0
                for i in range(10):
                    peak_try, charge_try = scope.scan()  # Get the peak value from the oscilloscope\
                    print(peak_try, charge_try)
                    peak += peak_try
                    charge += charge_try
                peak /= 10
                charge /= 10
                print(peak, charge)
                ### pulse peak measurement###
                peak_array[int((x - x_start) / step_size), int((y - y_start) / step_size), int((z - z_start) / step_size)] = peak
                charge_array[int((x - x_start) / step_size), int((y - y_start) / step_size), int((z - z_start) / step_size)] = charge
                print(f"Current position: X: {x_axis.get_position().Position}, Y: {y_axis.get_position().Position}, Z: {z_axis.get_position().Position}, pulse peak: {peak}, charge: {charge}")
    time.sleep(1)  # Wait for the motors to stop
    z_axis.command_move(0, 0)
    y_axis.command_move(0, 0)
    x_axis.command_move(0, 0)
    z_axis.command_wait_for_stop(10)
    y_axis.command_wait_for_stop(10)
    x_axis.command_wait_for_stop(10)
    np.save('xyz_peak.npy', peak_array)
    np.save('xyz_charge.npy', charge_array)


def yz_scan(y_axis, z_axis, y_start, y_end, z_start, z_end, step_size, scope):
    peak_array = np.zeros((int((y_end - y_start) / step_size) + 1, int((z_end - z_start) / step_size) + 1))
    charge_array = np.zeros((int((y_end - y_start) / step_size) + 1, int((z_end - z_start) / step_size) + 1))
    for z in range(z_start, z_end + 1, step_size):
        z_axis.command_move(-z, 0)
        z_axis.command_wait_for_stop(10)
        for y in range(y_start, y_end + 1, step_size):
            y_axis.command_move(y, 0)
            y_axis.command_wait_for_stop(10)

            peak, charge = 0, 0
            for i in range(10):
                peak_try, charge_try = scope.scan()  # Get the peak value from the oscilloscope
                print(peak_try, charge_try)
                peak += peak_try
                charge += charge_try
            peak /= 10
            charge /= 10
            print(peak, charge)
            ### pulse peak measurement###
            peak_array[int((y - y_start) / step_size), int((z - z_start) / step_size)] = peak
            charge_array[int((y - y_start) / step_size), int((z - z_start) / step_size)] = charge

            print(f"Current position: Y: {y_axis.get_position().Position}, Z: {z_axis.get_position().Position}, pulse peak: {peak}, charge: {charge}")

    time.sleep(1)  # Wait for the motors to stop
    z_axis.command_move(0, 0)
    y_axis.command_move(0, 0)
    z_axis.command_wait_for_stop(10)
    y_axis.command_wait_for_stop(10)
    np.save('yz_peak.npy', peak_array)
    np.save('yz_charge.npy', charge_array)

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
            for i in range(5):
                peak_try, charge_try = scope.scan()  # Get the peak value from the oscilloscope
                #print(peak_try, charge_try)
                peak += peak_try
                charge += charge_try
            peak /= 5
            charge /= 5

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

class Tektronix:
    def __init__(self, resource_name):
        self.rm = pyvisa.ResourceManager()
        try:
            self.inst = self.rm.open_resource(resource_name)
            self.inst.timeout = 10000
            self.idn = self.inst.query('*IDN?')
            print(f'Connected to {self.idn}')
            #self.inst.write('*cls') 
        except:
            print(f"Failed to connect to {resource_name}. Cheak the Ethernet connection, s'il vous plaît.")
            exit()

    def acquisition(self, nEvents):
   
        print('Acquiring waveforms...')
        for i in range(nEvents):
            if i % 10 == 0:
                print(f'Acquisition {i}/{nEvents}')
            self.runtheScope()
            data = {}
            for ch in range(1, 2):
                x, y = self.readChannel(ch)
                if ch == 1:
                    data['time'] = ak.Array([x])
                data[f'ch{ch}'] = ak.Array([y])

                # calculating pedestal mean and rms
                print(len(y))
                pedestal_total = np.sum(y[:400]) / 400 * len(y)
                pedestal_mean = np.mean(y[:400])
                pedestal_rms = np.std(y[:400])
                data[f'ch{ch}_ped_total'] = ak.Array([pedestal_total])
                data[f'ch{ch}_ped_mean'] = ak.Array([pedestal_mean])
                data[f'ch{ch}_ped_rms'] = ak.Array([pedestal_rms])

                # calculating collected charge
                collected_charge = (np.sum(y) * (x[1] - x[0])) - (pedestal_total * (x[1] - x[0])) * 1e15 / 50 # in fC
                data[f'ch{ch}_collected_charge'] = ak.Array([collected_charge])

                # finding the peak and toa time
                peak_index = np.argmax(-y)
                peak_value = y[peak_index]
                peak_time = x[peak_index]
                peak_voltage = np.max(-y)
                data[f'ch{ch}_peak_time'] = ak.Array([peak_time])
                data[f'ch{ch}_peak_voltage'] = ak.Array([peak_voltage])

                # calculating time of arrival (TOA) : 20% of the amplitude
                threshold = 0.2 * peak_value
                toa_indices = np.where(np.abs(y) > threshold)[0]
                if len(toa_indices) > 0:
                    toa_index = toa_indices[0]
                    toa_time = x[toa_index]
                    data[f'ch{ch}_toa_time'] = ak.Array([toa_time])
                else:
                    data[f'ch{ch}_toa_time'] = ak.Array([-99.0])  # No TOA found

            with uproot.recreate(f'temp/waveforms_temp_{i}.root') as f:
                f['Events'] = {k: ak.Array(v) for k, v in data.items()}
                #f['Events'] = ak.zip(data)

    def mergingROOT(self):
        tempdir = 'temp/'
        outdir = args.output_dir
        outname = args.output
        try:
            #os.system('hadd -f {}waveforms_merged.root {}waveforms_temp_*.root'.format(outdir, tempdir))
            os.system('hadd -f {}{} {}waveforms_temp_*.root'.format(outdir, outname, tempdir))
        except:
            print('Failed to merge the ROOT files')
            exit()
        os.system('rm -f {}waveforms_temp_*.root'.format(tempdir))

    def setTrigger(self, channel, level):
        self.inst.write(f'TRIG:A:LEVel:CH{channel} {level}')

    def setHorizontalWindow(self, window):
        self.inst.write(f'HOR:MAIN:SCALE {window}')

    def runtheScope(self):
        self.inst.write('ACQUIRE:STATE RUN')
        # Waiting for the acquisition to complete
        while int(self.inst.query('ACQUIRE:STATE?')) == 1:
            time.sleep(0.01)

    def readChannel(self, channel):
        self.inst.write(f'DATA:SOU CH{channel}')
        # waveform preamble
        x_increment = float(self.inst.query('WFMPRE:XINCR?'))
        x_origin = float(self.inst.query('WFMPRE:XZERO?'))
        y_multiplier = float(self.inst.query('WFMOUTPRE:YMULT?'))
        y_origin = float(self.inst.query('WFMOUTPRE:YZERO?'))
        y_offset = float(self.inst.query('WFMOUTPRE:YOFF?'))
        #print(x_origin, x_increment)
        # waveform data

        waveform_data = self.inst.query_binary_values('CURVE?', datatype='b', container=np.array)
        #if channel == 1:
        #    print(waveform_data, y_offset, y_multiplier, y_origin)
        #y_data = (waveform_data)
        #y_data = (waveform_data - y_offset) * y_multiplier + y_origin
        y_data = (np.array(waveform_data, dtype='double') - y_offset) * y_multiplier + y_origin
        x_data = x_origin + np.arange(len(y_data)) * x_increment - (len(y_data) * x_increment) / 2

        #waveform_data = self.inst.query_binary_values('CURVE?', datatype='B', container=np.array)
        # x 축 데이터 계산
        #x_data = np.array([x_origin + i * x_increment for i in range(len(waveform_data))])

        # y 축 데이터 계산
        #y_data = (waveform_data - y_offset) * y_multiplier + y_origin
        #y_data = waveform_data

        #y_data = (waveform_data - y_offset) * y_multiplier + y_origin
        #x_data = x_origin + np.arange(len(y_data)) * x_increment - (len(y_data) * x_increment) / 2
        dqmDraw(channel, x_data, y_data)
        return x_data, y_data

    def scan(self):
        self.runtheScope()
        data = {}
        ch = 2
        x, y = self.readChannel(ch)
        #data[f'ch{ch}'] = ak.Array([y])
        # calculating pedestal mean and rms
        pedestal_mean = np.mean(y[:400])
        pedestal_total = pedestal_mean * len(y)
        collected_charge = ((np.sum(y) * (x[1] - x[0])) - (pedestal_total * (x[1] - x[0]))) * 1e15 / 50 # in fC
        #print('Collected charge:', collected_charge, 'fC')
        #print(len(y))
        window_size = 200
        peak_voltage = abs(np.min(y[600:int(400   + window_size)]) - pedestal_mean)
        return peak_voltage, collected_charge

#####################################################################################################################3

# Start time
start_time = time.time()

# default settings
resource_name = 'TCPIP::192.168.0.2::INSTR' ## 내부망 IP 주소 (사전 정의됨. 바꾸지 마시오.)
horizontalwindow = 5e-9
trigger_channel = 1
trigger_level = -0.4

# default Keithely 2470 setting


if __name__ == '__main__':
    scope = Tektronix(resource_name)
    scope.setHorizontalWindow(horizontalwindow)
    scope.setTrigger(trigger_channel, trigger_level)

    # Device URI 설정
    device_uri3 = "xi-com:/dev/ttyACM0"  # Y
    device_uri2 = "xi-com:/dev/ttyACM1"  # X 
    device_uri1 = "xi-com:/dev/ttyACM2"  # Z

    #device_uri1 = "/dev/ttyACM0"  # Z
    #device_uri2 = "/dev/ttyACM1"  # X
    #device_uri3 = "/dev/ttyACM2"  # Y

    # Axis 객체 생성
    z_axis = ximc.Axis(device_uri1)
    x_axis = ximc.Axis(device_uri2)
    y_axis = ximc.Axis(device_uri3)

    # Device 열기
    z_axis.open_device()
    x_axis.open_device()
    y_axis.open_device()

    # 위치 0으로 설정
    x_axis.command_zero()
    y_axis.command_zero()
    z_axis.command_zero()

    # 스캔 범위
    #scan_range = int(500 * 1.2)

    # XY 스캔 실행
    #xy_scan(x_axis, y_axis, -20, 20, -20, 20, 2,scope)
    xyz_scan(x_axis, y_axis, z_axis, -15, 15, -15, 15, -15, 15, 5, scope)

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