import time
import pyvisa as visa
import matplotlib.pyplot as plt
import numpy as np

visa_address = 'TCPIP::192.168.0.2::INSTR'

rm = visa.ResourceManager()
scope = rm.open_resource(visa_address)
scope.timeout = 100000  # ms
scope.encoding = 'latin_1'
scope.read_termination = '\n'
scope.write_termination = None
scope.write('*cls')  # clear ESR

print(scope.query('*idn?'))

#scope.write('HOR:MAIN:SCALE 1e-8')  # x-axis scale

# io config
scope.write('header 0')
scope.write('data:encdg SRIBINARY')
scope.write('data:start 1')
record = int(scope.query('horizontal:recordlength?'))
scope.write(f'data:stop {record}')
scope.write('wfmoutpre:byt_n 1')

# acq config
scope.write('acquire:state 0')
scope.write('acquire:stopafter SEQUENCE')
scope.write('acquire:state 1')
scope.query('*opc?')

# CH1 data
scope.write('data:source CH1')
bin_wave1 = scope.query_binary_values('curve?', datatype='b', container=np.array)
tscale1 = float(scope.query('wfmoutpre:xincr?'))
tstart1 = float(scope.query('wfmoutpre:xzero?'))
vscale1 = float(scope.query('wfmoutpre:ymult?'))
voff1 = float(scope.query('wfmoutpre:yzero?'))
vpos1 = float(scope.query('wfmoutpre:yoff?'))

# CH2 data
scope.write('data:source CH2')
bin_wave2 = scope.query_binary_values('curve?', datatype='b', container=np.array)
tscale2 = float(scope.query('wfmoutpre:xincr?'))
tstart2 = float(scope.query('wfmoutpre:xzero?'))
vscale2 = float(scope.query('wfmoutpre:ymult?'))
voff2 = float(scope.query('wfmoutpre:yzero?'))
vpos2 = float(scope.query('wfmoutpre:yoff?'))

# CH3 data
scope.write('data:source CH3')
bin_wave3 = scope.query_binary_values('curve?', datatype='b', container=np.array)
tscale3 = float(scope.query('wfmoutpre:xincr?'))
tstart3 = float(scope.query('wfmoutpre:xzero?'))
vscale3 = float(scope.query('wfmoutpre:ymult?'))
voff3 = float(scope.query('wfmoutpre:yzero?'))
vpos3 = float(scope.query('wfmoutpre:yoff?'))

# CH4 data
scope.write('data:source CH4')
bin_wave4 = scope.query_binary_values('curve?', datatype='b', container=np.array)
tscale4 = float(scope.query('wfmoutpre:xincr?'))
tstart4 = float(scope.query('wfmoutpre:xzero?'))
vscale4 = float(scope.query('wfmoutpre:ymult?'))
voff4 = float(scope.query('wfmoutpre:yzero?'))
vpos4 = float(scope.query('wfmoutpre:yoff?'))


# error checking
r = int(scope.query('*esr?'))
print('event status register: 0b{:08b}'.format(r))
r = scope.query('allev?').strip()
print('all event messages: {}'.format(r))

scope.close()
rm.close()

# create scaled vectors
# horizontal (time) → CH1 기준 사용
total_time = tscale1 * record
tstop = tstart1 + total_time
scaled_time = np.linspace(tstart1, tstop, num=record, endpoint=False)

# vertical (voltage)
scaled_wave1 = (np.array(bin_wave1, dtype='double') - vpos1) * vscale1 + voff1
scaled_wave2 = (np.array(bin_wave2, dtype='double') - vpos2) * vscale2 + voff2
scaled_wave3 = (np.array(bin_wave3, dtype='double') - vpos3) * vscale3 + voff3
scaled_wave4 = (np.array(bin_wave4, dtype='double') - vpos4) * vscale4 + voff4

# plotting
plt.figure(figsize=(10, 6))
plt.plot(scaled_time, scaled_wave1, label='Channel 1', color='gold')
plt.plot(scaled_time, scaled_wave2, label='Channel 2', color='blue')
plt.plot(scaled_time, scaled_wave3, label='Channel 3', color='purple')
plt.plot(scaled_time, scaled_wave4, label='Channel 4', color='green')
plt.grid()
plt.xlabel('Time (s)')
plt.xlim(scaled_time[0], scaled_time[-1])
plt.ylabel('Voltage (V)')
plt.legend()
plt.savefig("test.png")
print("look for plot window...")

print("\nend of demonstration")
