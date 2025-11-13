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
    return 'v0.0'

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
            self.inst.timeout = 30000
            self.idn = self.inst.query('*IDN?')
            print(f'Connected to {self.idn}')
            try:
                print('trying to reset the registry...')
                self.resistry_reset()
            except Exception as e:
                print(f'Failed to reset the registry. Please check the connection. Error: {e}')
                exit()
        except Exception as e:
            print(f"Failed to connect to {resource_name}. Cheak the Ethernet connection, s'il vous plaît. Error: {e}")
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

    def check_active_channels(self):
        status = []
        for ch in range(1, 5):  # 채널 1~4 확인
            state = int(self.inst.query(f'CHAN{ch}:DISP?')) ### need to check this command work. ###
            status.append(state)  # 0 or 1
            if state not in [0, 1]:
                print(f'Channel {ch} status is invalid: {state}')
                sys.exit(1)
            if sum(status) == 0: # if sum of status is 0, no active channels so error
                print('No active channels found. Please check the channel settings.')
                sys.exit(1)
        return status

    def acquisition(self, nEvents):

        print(f'Horizontal window: {horizontalwindow} sec', f'Trigger channel: {trigger_channel}', f'Trigger level: {trigger_level} V')
        self.inst.write(f'ACQUIRE:STATE STOP; DATA:ENC RPB; HOR:MAIN:SCALE {horizontalwindow}')            
        print('Checking active channels...')
        #status = self.check_active_channels()  # 여기서 status 받아옴
        status = [0,1,0,0]  # for test
        active_channels = [i+1 for i, val in enumerate(status) if val == 1]
        print(f'Active channels: {active_channels}')
        print('Acquiring waveforms...')
        intermediate_idx = 0
        # try to check the BUFFER directory is exist
        tempdir = 'BUFFER/'
        if not os.path.exists(tempdir):
            print("the BUFFER directory does not exist. creating one... (someone deleted BUFFER directory?)")
            os.makedirs(tempdir)

        # predefined variables
        dummy_line = " ".join([str(9999)] * 1000) + "\n"
        time_scale = 1e-9  # time scale in ns
        voltage_scale = 1e-6  # voltage scale in uV

        for i in tqdm(range(nEvents//5), desc='Acquiring', unit='event'):
            if i > 9999:
                raise ValueError("Event index exceeds 4 digits! (i > 9999)")
            out_file = f"{tempdir}/data_{i+1:05d}.txt"
            # txt data writing start
            with open(out_file, 'w') as f: # make txt file
                count = 0
                while count < 5: # txt loop start
                    self.runtheScope() # one scan
                    if count == 0 : ## first loop additional time information writing
                        f.write("#time\n")
                        for ch in range(1,5):
                            if status[ch-1] == 0:
                                    f.write(f"CH_{ch} 1\n")
                                    f.write(dummy_line)
                            elif status[ch-1] == 1:
                                    x, _ = self.readChannel(ch)
                                    print(len(x))
                                    f.write(f"CH_{ch} {time_scale}\n")
                                    f.write(" ".join(map(str,x/time_scale)) + "\n")
                            else :
                                print("txt writing error, exit...")
                                sys.exit(1)

                    if count == 0 :
                        f.write(f"#waveform\n")
                    f.write(f"Event_ID {str(5*i+count + 1)}\n")

                    for ch in range(1,5):
                        if status[ch-1] == 0:
                            f.write(f"CH_{ch} 1\n")
                            f.write(dummy_line)
                        elif status[ch-1] == 1:
                                _, y = self.readChannel(ch)
                                f.write(f"CH_{ch} {voltage_scale}\n")
                                f.write(" ".join(map(str,y/voltage_scale)) + "\n")
                        else :
                            print("channel writing error, exit...")
                            sys.exit(1)
                    count = count + 1

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
parser.add_argument('--horizontalwindow', type=float, default=1e-9, help='Horizontal window')
parser.add_argument('--trigger_channel', type=int, default=2, help='Trigger channel')
parser.add_argument('--trigger_level', type=float, default=-0.000100, help='Trigger level')
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
            #scope.mergingROOT() i dont make root file so dont need this
            ## Save the output file with the scan value
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