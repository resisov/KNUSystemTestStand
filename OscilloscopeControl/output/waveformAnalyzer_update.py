import uproot # type: ignore
import numpy as np # type: ignore
import awkward as ak # type: ignore
import matplotlib.pyplot as plt # type: ignore
import mplhep as hep # type: ignore
#import scipy
from scipy.optimize import curve_fit # type: ignore
import os, sys
import glob

def gaussian(x, a, b, c):
    return a*np.exp(-(x-b)**2/(2*c**2))

def linear(x, a, b):
    return a*x + b

def waveformAnalyzer(file, channel):
    f = uproot.open(file)
    tree = f['Events']
    collected_charge = tree['ch1_collected_charge'].array()
    ped_rms = tree['ch1_ped_rms'].array()
    irrad_index = 'Pre-Irrad'
    # reject events that has ped_rms greater then mean + 3* std
    ped_rms_mean = np.mean(ped_rms)
    ped_rms_std = np.std(ped_rms)
    mask = (ped_rms < ped_rms_mean + 3 * ped_rms_std) & (ped_rms > ped_rms_mean - 3 * ped_rms_std)
    charge = collected_charge[mask]
    charge_original = collected_charge # original

    #print("from ",file,",",len(mask[mask == False]), 'events are masekd')
    #print("masked charge mean: ", np.mean(charge), "original charge mean: ", np.mean(charge_original))

    plt.style.use(hep.style.ROOT)
    plt.figure(figsize=(8, 8))
    mean = np.mean(charge)
    std = np.std(charge)
    histo = plt.hist(charge, range=(mean-3*std, mean+12*std), bins=150 ,histtype='stepfilled', edgecolor='black', color = '#3D74B6', linewidth=2, label='$\mathbf{UFSD-K2}$ $\mathbf{Wafer2}$ $\mathbf{LGAD}$'+"\nLaser Width @ 81.2%\nBias Voltage: "+str(file.split('_')[-1].replace('.root', ''))+"V\n"+irrad_index)
    plt.xlabel('Collected Charge (fC)')
    plt.ylabel('Counts')
    # fit gaussian range = -60 to 0
    x = histo[1][:-1]
    y = histo[0]

    sopt, pcov = curve_fit(gaussian, x, y, p0=[100, mean, std])
    plt.plot(x, gaussian(x, *sopt), '-', label='$\mathbf{Gaussian Fit}$\n'+r'$\mu=%.2f$' % sopt[1]+'\n'+r'$\sigma=%.2f$' % abs(sopt[2]), linewidth=3, color='#DC3C22')

    # peak position
    peak_pos = sopt[1]
    obs_sigma = abs(sopt[2])
    plt.legend()
    plt.grid()
    # change file name
    out_name = file.split('/')[0] +'_'+ file.split('/')[1].replace('.root', '')
    plt.savefig('plots/'+str(out_name)+'.pdf')
    plt.close()
    bv = int(file.split('_')[-1].replace('.root', ''))
    #print('Bias Voltage: ', bv)

    return bv, sopt[1], abs(sopt[2])

if __name__ == "__main__":
    flist = glob.glob('k2_PIN_251120/*.root')
    bv_val, mean_val, std_val = [], [], []
    for f in flist:
        bv, mean, std = waveformAnalyzer(f, 1)
        bv_val.append(bv)
        mean_val.append(mean)
        print(bv, abs(mean))
        std_val.append(std)

    # plot collected charge vs bias voltage
    plt.figure(figsize=(8, 8))
    plt.style.use(hep.style.ROOT)
    plt.errorbar(bv_val, np.abs((np.array(mean_val))),xerr=5, yerr=std_val, fmt='o', color='blue', label='UFSD-LF Wafer2 Pre-Irrad', markersize=10)

    plt.xlabel('Bias Voltage (V)')
    plt.ylabel('Collected Charge (fC)')
    plt.legend(loc = 'upper left')
    plt.grid()
    plt.tight_layout()
    plt.savefig('collected_charge_vs_bias_voltage.pdf')

    pin_gain = 12.01
    # plot gain ratio
    plt.figure(figsize=(8, 8))
    plt.style.use(hep.style.ROOT)
    plt.errorbar(bv_val, np.abs(np.array(mean_val))/pin_gain, xerr=5, yerr=np.array(std_val)/pin_gain, fmt='o', color='blue', label='UFSD-LF Wafer2 Pre-Irrad', markersize=10)
    # Fill between mean +/- std
    plt.xlabel('Bias Voltage (V)')
    plt.ylabel('Gain (LGAD/PIN)')
    plt.legend(loc = 'upper left')
    plt.grid()
    plt.tight_layout()
    plt.savefig('gain_ratio_vs_bias_voltage.pdf')
