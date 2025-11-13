# -*- coding: utf-8 -*-
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

def __version__():
    return 'v0.6'

def __developer__():
    return 'Taiwoo Kim & Jongyeob Kim'

def __target__():
    return 'Tektronix Series Oscilloscope'

def dqmDraw(channel, x, y):
    plt.style.use(hep.style.ROOT)
    plt.figure(figsize=(10, 6))
    hep.cms.label(llabel='KNU DQM', rlabel='')
    if channel == 1:
        color = 'yellow'
    elif channel == 2:
        color = 'blue'
    elif channel == 3:
        color = 'purple'
    elif channel == 4:
        color = 'green'
    else:
        raise ValueError('Invalid channel number')
    x = x * 1e11
    print(x[:10])
    print(y[:10])
    plt.plot(x, y, color=color)
    plt.xlim(-100,-99)
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
        except:
            print(f"Failed to connect to {resource_name}. Cheak the Ethernet connection, s'il vous plaît.")
            exit()

    def acquisition(self, nEvents):
        print(f'Horizontal window: {horizontalwindow} sec', f'Trigger channel: {trigger_channel}', f'Trigger level: {trigger_level} V')
        self.inst.write(f'ACQUIRE:STATE STOP; DATA:ENC RPB; HOR:MAIN:SCALE {horizontalwindow}; TRIG:A:LEVel:CH{trigger_channel} {trigger_level}')            
        print('Acquiring waveforms...')
        for i in range(nEvents):
            if i % 10 == 0:
                print(f'Acquisition {i}/{nEvents}')
            self.runtheScope()
            data = {}
            for ch in range(1, 5):
                x, y = self.readChannel(ch)
                if ch == 1:
                    data['time'] = ak.Array([x])
                data[f'ch{ch}'] = ak.Array([y])
            with uproot.recreate(f'temp/waveforms_temp_{i}.root') as f:
                f['Events'] = ak.zip(data)

    def mergingROOT(self):
        tempdir = 'temp/'
        outdir = 'output/'
        try:
            os.system('hadd -f {}waveforms_merged.root {}waveforms_temp_*.root'.format(outdir, tempdir))
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
            time.sleep(0.1)

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
            #print(waveform_data[:10])
        y_data = (waveform_data)
        #y_data = (waveform_data - y_offset) * y_multiplier + y_origin
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

# Argument parser
parser = argparse.ArgumentParser(description='Oscilloscope control')
parser.add_argument('--nEvents', type=int, default=10, help='Number of events to acquire')
parser.add_argument('--horizontalwindow', type=float, default=1e-8, help='Horizontal window')
parser.add_argument('--trigger_channel', type=int, default=2, help='Trigger channel')
parser.add_argument('--trigger_level', type=float, default=-0.4, help='Trigger level')
args = parser.parse_args()

# Start time
start_time = time.time()

# default settings
resource_name = 'TCPIP::192.168.0.2::INSTR' ## 내부망 IP 주소 (사전 정의됨. 바꾸지 마시오.)
horizontalwindow = args.horizontalwindow
trigger_channel = args.trigger_channel
trigger_level = args.trigger_level

if __name__ == '__main__':
    print(f'Version: {__version__()}')
    print(f'Developer: {__developer__()}')
    print(f'Target: {__target__()}')
    print('')
    scope = Tektronix(resource_name)
    scope.setHorizontalWindow(horizontalwindow)
    scope.setTrigger(trigger_channel, trigger_level)
    scope.acquisition(args.nEvents)
    scope.mergingROOT()

    # End time
    print('File saved on "output/" directory')
    end_time = time.time()
    print(f'Elapsed time: {end_time - start_time:.2f} sec')
    exit()