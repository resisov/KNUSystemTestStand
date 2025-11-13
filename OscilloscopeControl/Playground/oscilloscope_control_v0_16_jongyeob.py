# 1) v16 goal : 측정 끝나자마자 바로 pedestal, waveform 플롯 pdf 형식으로 생성
# -*- coding: utf-8 -*-
import os, sys
from tqdm import tqdm
import pyvisa
import time
import numpy as np
import uproot
import argparse
import awkward as ak
import utils.artwork as artwork
from utils.Keithely2470 import Keithely
import matplotlib.pyplot as plt
import mplhep as hep
from scipy.optimize import curve_fit
import subprocess

def __version__():
    return 'v0.16'

def __developer__():
    return 'Taiwoo Kim and Jongyeob Kim'

def __target__():
    return 'Tektronix Series Oscilloscope'

def sigmoid(x, a, b, c):
    """Sigmoid function for curve fitting."""
    return c / (1 + np.exp(-a * (x - b)))

def gaussian(x, amp, mean, sigma):
    """Gaussian function for curve fitting."""
    return -(amp * np.exp(-((x - mean) ** 2) / (2 * sigma ** 2)))

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
    y = y * 1e3  # Convert to mV
    plt.plot(x, y, color=color)
    plt.xlabel('Time (ns)')
    plt.ylabel('Voltage (mV)')
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
            try:
                print('trying to reset the registry...')
                self.resistry_reset()
            except:
                print('Failed to reset the registry. Please check the connection.')
                exit()
        except:
            print(f"Failed to connect to {resource_name}. Cheak the Ethernet connection, s'il vous plaît.")
            exit()

    def resistry_reset(self):
        self.inst.encoding = 'latin_1'
        self.inst.read_termination = '\n'
        self.inst.write_termination = None
        self.inst.write('*CLS')  # Clear the status register
        # io config
        self.inst.write('HEADER 0')  # Disable header
        self.inst.write('DATA:ENCODING SRIBINARY')  # Set data encoding
        self.inst.write('DATA:START 1')  # Set start point
        record_length = int(self.inst.query('HORizontal:RECOrdlength?'))  # Get record length
        self.inst.write(f'DATA:STOP {record_length}')  # Set stop point
        self.inst.write('WFMOUTPRE:BYT_N 1')  # Set byte number for waveform output
        # acq config
        self.inst.write('ACQUIRE:STATE STOP')  # Stop acquisition
        self.inst.write('ACQUIRE:STOPAFTER SEQUENCE')  # Set stop after sequence
        self.inst.write('ACQUIRE:STATE RUN')  # Start acquisition
        self.inst.query('*OPC?')  # Wait for operation complete
        # ch1 data
        self.inst.write('DATA:SOU CH2')  # Set source to channel 1
        bin_wave1 = self.inst.query_binary_values('CURVE?', datatype='b', container=np.array)
        tscale1 = float(self.inst.query('WFMOUTPRE:XINCR?'))  # Time scale
        tstart1 = float(self.inst.query('WFMOUTPRE:XZERO?'))  # Time start
        vscale1 = float(self.inst.query('WFMOUTPRE:YMULT?'))  # Voltage scale
        voff1 = float(self.inst.query('WFMOUTPRE:YZERO?'))  # Voltage offset
        vpos1 = float(self.inst.query('WFMOUTPRE:YOFF?'))  # Voltage position
        
        total_time = tscale1 * record_length # Total time in ns
        tstop = tstart1 + total_time  # Time stop
        scaled_time = np.linspace(tstart1, tstop, record_length)  # Scaled time array
        scaled_waveform = (np.array(bin_wave1, dtype='double') - vpos1) * vscale1 + voff1  # Scaled waveform data
        dqmDraw(1, scaled_time, scaled_waveform)  # Draw waveform for channel 1

    def acquisition(self, nEvents):
        print(f'Horizontal window: {horizontalwindow} sec', f'Trigger channel: {trigger_channel}', f'Trigger level: {trigger_level} V')
        self.inst.write(f'ACQUIRE:STATE STOP; DATA:ENC RPB; HOR:MAIN:SCALE {horizontalwindow}')            
        #self.inst.write(f'ACQUIRE:STATE STOP; DATA:ENC RPB; HOR:MAIN:SCALE {horizontalwindow}; TRIG:A:LEVel:CH{trigger_channel} {trigger_level}')            

        print('Acquiring waveforms...')


        intermediate_idx = 0
        tempdir = 'temp/'
        batch_files = []

        for i in tqdm(range(nEvents), desc='Acquiring', unit='event'):
            self.runtheScope()
            data = {}
            for ch in range(1, 3):
                x, y = self.readChannel(ch)
                if ch == 1:
                    data['time'] = ak.Array([x])
                data[f'ch{ch}'] = ak.Array([y])

                # finding the peak and toa time
                peak_index = np.argmax(np.abs(y))
                peak_value = y[peak_index]
                peak_time = x[peak_index]
                peak_voltage = np.max(np.abs(y))

                # collected charge range: # 50 points before and after the peak
                # calculating peak voltage, time and index
                data[f'ch{ch}_peak_volt'] = ak.Array([peak_voltage])
                data[f'ch{ch}_peak_time'] = ak.Array([peak_time])
                data[f'ch{ch}_peak_index'] = ak.Array([peak_index])

                integral = np.sum(y[peak_index - 50:peak_index + 50]) * (x[1] - x[0])  

                # calculating pedestal mean and rms
                pedestal_total = np.sum(y[:400]) / 400 * 100 ###### 주의! "* 100" 이 값은 바로 윗줄 적분 범위를 하드 코딩한 값입니다.
                pedestal_mean = np.mean(y[:400])
                pedestal_rms = np.std(y[:400])
                data[f'ch{ch}_ped_total'] = ak.Array([pedestal_total])
                data[f'ch{ch}_ped_mean'] = ak.Array([pedestal_mean])
                data[f'ch{ch}_ped_rms'] = ak.Array([pedestal_rms])

                # calculating collected charge
                collected_charge = (integral - (pedestal_total * (x[1] - x[0]))) * 1e15 / 5000 # in fC
                data[f'ch{ch}_collected_charge'] = ak.Array([collected_charge])

                # waveform fitting with gaussian
                try:
                    fit_x = x[peak_index - 50:peak_index + 50]
                    fit_y = y[peak_index - 50:peak_index + 50]
                    popt, _ = curve_fit(gaussian, fit_x, fit_y, p0=[peak_voltage, peak_time, 1e-9], maxfev=10000)
                    fit_amp, fit_mean, fit_sigma = popt
                    fit_curve = gaussian(x, fit_amp, fit_mean, fit_sigma)
                    # 20% of peak value for threshold = mean - 1.794 * sigma
                    toa_time = fit_mean - (1.794 * fit_sigma)
                    #print(f'toa_index: {toa_time}')
                    data[f'ch{ch}_toa'] = ak.Array([toa_time])
                except:
                    #print(f'Fit failed for channel {ch} and event {i}. Skipping fit.')
                    data[f'ch{ch}_toa'] = ak.Array([-99.0])  # Placeholder for failed fit


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

        waveform_data = self.inst.query_binary_values('CURVE?', datatype='b', container=np.array)
        y_data = (np.array(waveform_data, dtype='double') - y_offset) * y_multiplier + y_origin
        x_data = x_origin + np.arange(len(y_data)) * x_increment - (len(y_data) * x_increment) / 2

        #dqmDraw(channel, x_data, y_data)
        return x_data, y_data

# Argument parser
parser = argparse.ArgumentParser(description='Oscilloscope control')
parser.add_argument('--nEvents', type=int, default=10, help='Number of events to acquire')
parser.add_argument('--horizontalwindow', type=float, default=10e-10, help='Horizontal window')
parser.add_argument('--trigger_channel', type=int, default=2, help='Trigger channel')
parser.add_argument('--trigger_level', type=float, default=-0.000080, help='Trigger level')
parser.add_argument('--output_dir', type=str, default='/home/knutimingdaq01/Desktop/KNUSystemTestStand/OscilloscopeControl/output/', help='Output directory')
parser.add_argument('--output', type=str, default='waveforms_merged.root', help='Output name')
parser.add_argument('--scan', type=str, default='False', help='Scan mode (True/False)')
parser.add_argument('--scan_start', type=float, default=-140, help='Scan start value')
parser.add_argument('--scan_stop', type=float, default=-140, help='Scan stop value')
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
    ## output directory check
    if not os.path.exists(args.output_dir):
        os.makedirs(args.output_dir)
    if args.scan == 'False':
        scope = Tektronix(resource_name)
        scope.setHorizontalWindow(horizontalwindow)
        scope.setTrigger(trigger_channel, trigger_level)
        scope.acquisition(args.nEvents)
        scope.mergingROOT()
    else:
        keithely = Keithely()
        keithely.reset_voltage()  # Reset the voltage to 0V before starting the scan
        keithely.apply_voltage(args.scan_start)  # Apply the starting voltage
        for i in tqdm(np.arange(args.scan_start, args.scan_stop-1, -10), desc='Scanning', unit='step'):
            print(f'Scanning: {i} V')
            # Adjust the voltage for each step
            scope = Tektronix(resource_name)
            scope.setHorizontalWindow(horizontalwindow)
            scope.setTrigger(trigger_channel, trigger_level)
            scope.acquisition(args.nEvents)
            scope.mergingROOT()
            ## Save the output file with the scan value
            output_file = f'{args.output_dir}waveforms_scan_{int(abs(i))}.root'
            os.rename(f'{args.output_dir}{args.output}', output_file)
            keithely.adjust_voltage(-10)
            time.sleep(0.5)
        # Reset the voltage to 0V after the scan
        print('Scan completed. Resetting voltage to 0V.')
        keithely.reset_voltage()  # Reset the voltage to 0V after the scan

    # End time
    print('File saved on "output/" directory')
    end_time = time.time()
    print(f'Elapsed time: {end_time - start_time:.2f} sec')
    exit()