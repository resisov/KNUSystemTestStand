import matplotlib.pyplot as plt
import numpy as np
import mplhep as hep

plt.style.use(hep.style.ROOT)
#Vbias = np.array([170,180,190,200,210,220,230,240,250,260])
#Qc = np.array([38.35,38.94,37.57,37.07,37.45,36.66,36.43,36.21,33.31,33.49])

Vbias = np.array([140,150,160,170,180,190,200,210,220,230,240])
woamp = np.array([0.05633862,0.05095725,0.04577215,0.04519149,0.0418785 ,0.0404607 ,
 0.03609882,0.03111225,0.02922028,0.02946326,0.02744112])*1000
wamp = np.array([0.04454275,0.03818286,0.03881641,0.03552538,0.03176936,0.03162596,
 0.03122948,0.02979534,0.02906873,0.02890729,0.02782265])*1000
#amp_lense = np.array([0.20680368,0.20549568,0.1813013 ,0.16820922,0.15390044,0.13928859,
# 0.1302488 ,0.12818376,0.11434274,0.09937145,0.09668498])*1000
#noamp_lense = np.array( [0.22932396,5.95800694,0.39300965,0.3015493 ,0.28045074,0.21954266,
# 0.19772168,0.16392583,0.13437826,0.10991214,0.08761916])*1000

#Vbias = np.array([140,160,170,180,190,200,210,220,230,240])
#woamp = np.array([0.05633862,0.04577215,0.04519149,0.0418785 ,0.0404607 ,
# 0.03609882,0.03111225,0.02922028,0.02946326,0.02744112])*1000
#wamp = np.array([0.04454275,0.03881641,0.03552538,0.03176936,0.03162596,
# 0.03122948,0.02979534,0.02906873,0.02890729,0.02782265])*1000
#amp_lense = np.array([0.20680368,0.1813013 ,0.16820922,0.15390044,0.13928859,
# 0.1302488 ,0.12818376,0.11434274,0.09937145,0.09668498])*1000
#noamp_lense = np.array( [0.2293239,0.39300965,0.3015493 ,0.28045074,0.21954266,
# 0.19772168,0.16392583,0.13437826,0.10991214,0.08761916])*1000


plt.xlabel('Bias Voltage [V]')
plt.ylabel("Time resolution [ps]")
plt.plot(Vbias, woamp, 'black',marker='o',markerfacecolor='white',markeredgecolor='black',linestyle='--', label='UFSD-LF pre-irrad')
plt.plot(Vbias, wamp, 'black',marker='o',linestyle='-', label="UFSD-LF pre-irrad (amp)")

#plt.plot(Vbias, noamp_lense, 'blue',marker='o',markerfacecolor='white',markeredgecolor='blue',linestyle='--', label='UFSD-LF pre-irrad with filter')
#plt.plot(Vbias, amp_lense, 'blue',marker='o',linestyle='-', label="UFSD-LF pre-irrad with filter (amp)")

plt.legend()
plt.savefig("test.png")