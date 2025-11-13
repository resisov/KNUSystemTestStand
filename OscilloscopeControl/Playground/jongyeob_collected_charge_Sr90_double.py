import uproot
import numpy as np
import awkward as ak
import scipy
from scipy.optimize import curve_fit
import os
import sys
from scipy.stats import norm
import traceback
import matplotlib.pyplot as plt
import glob
import re
import mplhep as hep

def mixed(x, A1, A2, mpv1, mpv2, eta1, eta2,C=0):
    return gaussian(x, A1, mpv1, eta1) + landau(x, A2, mpv2, eta2) + C

def landau(x, A, mpv, eta):
    return A * np.exp(-0.5 * ((x - mpv) / eta + np.exp(-(x - mpv) / eta)))

def gaussian(x, amp, mean, sigma):
    return amp * np.exp(-((x - mean) ** 2) / (2 * sigma ** 2))

files = glob.glob('/home/knutimingdaq01/Desktop/KNUSystemTestStand/OscilloscopeControl/output/LF_PreIrrad_Sr90_glich_100uV_BW/*.root')


v = []
for path in files:
    match = re.search(r'_(\d+)\.root$', path)
    if match:
        v.append(int(match.group(1)))
    else:
        print(f"⚠️ 파일명에서 전압 못 찾음: {path}")

v = np.array(v)
files = np.array(files)

sorted_indices = np.argsort(v)
v_sorted = v[sorted_indices].tolist()
f_sorted = files[sorted_indices].tolist()
# array for selected data

path = os.path.dirname(f_sorted[0])
collected_charge = np.array([]) # sigma calculated using formula
charge_sigma = np.array([]) # sigma calculated using formula
#gain = np.array([12,17,26,40])
#print("\n \033[1;34mWill skip events with peak time outside the range of 7 ns to 13 ns.\033[0m\n")
for j in range(len(v_sorted)): # file loop

    print(f"Processing file {j+1}/{len(v_sorted)}: {f_sorted[j]}")
    data = uproot.open(f_sorted[j])
    fname = os.path.splitext(os.path.basename(f_sorted[j]))[0]
    time = data["Events"]["time"].array()
    waveform = -data['Events']['ch2'].array()
    factor = len(time[0]) / 1000
    # reset array
    peak_v = np.array([])
    timestamp = np.array([])
    for i in range(len(waveform)): # event loop
        x = np.array(time[i])
        y = np.array(waveform[i])  # compensate for wrong impedance divide

        ped_mean = np.mean(y[:100*int(factor)])
        ped_rms = np.std(y[:100]*1e+3*int(factor))
        #print(ped_rms)
        if ped_rms > 0.05:
            #print(f'Skipping event {i} due to high pedestal RMS: {ped_rms}')
            timestamp = np.append(timestamp, -99.0)
            continue

        y = y - ped_mean
        peak_index = np.argmax(np.abs(y))
        peak_value = y[peak_index]
        peak_time = x[peak_index]
        min_voltage = np.max(y)
        #print(min_voltage)
#        if (peak_time) < 0.7e-8 or (peak_time) > 1.2e-8:
        if (peak_time) < 0 or (peak_time) > 1.0e-9:
            timestamp = np.append(timestamp, -99.0)
            continue

        if min_voltage < 8e-4 :
            timestamp = np.append(timestamp, -99.0)
            continue

        peak_voltage = np.max(y)
        matching_indices = ak.where(y < 0)[0]

        #before = np.max(matching_indices[matching_indices <  peak_index])  # Find the maximum index before the peak index
        #after = np.min(matching_indices[matching_indices > peak_index])  # Find the minimum index after the peak index

        before = peak_index - (100*int(factor))  # Find the maximum index before the peak index
        after = peak_index + (200*int(factor))  # Find the minimum index after the peak index
        print(f'Event {i}: peak_index={peak_index}, before={before}, after={after}, len(y)={len(y)}')
        print("hello world")

        #print("before : ", peak_index - before,"after : ", after - peak_index)

        try:
            fit_x = np.asarray(x[before:after]) # fitting range
            fit_y = np.asarray(y[before:after])

            charge = np.sum(fit_y) * (fit_x[1] - fit_x[0]) * 1e+15 / 50
            #popt, _ = curve_fit(gaussian, fit_x, fit_y, p0=[peak_voltage, peak_time, 1e-9], maxfev=10000)
            #fit_amp, fit_mean, fit_sigma = popt
              # convert to ns
            timestamp = np.append(timestamp,charge)

        except:
            #print(f'Fit failed for channel 2 and event {i}. Skipping fit. case1')
            timestamp = np.append(timestamp, -99.0)  # Placeholder for failed fit

    # masking failed events
    mask = (timestamp != -99.0)
    timestamp = timestamp[mask]
    mu = np.mean(timestamp)
    std = np.std(timestamp)
    #print(mu,std)
    bin_width = 3
    counts, bins = np.histogram(timestamp, bins = np.arange(0, 300 + bin_width,bin_width))
    #print(bins)
    ben_center = (bins[:-1] + bins[1:]) / 2
    p0 = [100, 50, 2, 4, 2, 4]
    #print("bin centors: ", ben_center)
    #print(p0)
    popt, _ = curve_fit(mixed, ben_center, counts, p0=p0, maxfev=10000) # fitting
    timestamp_amp, amp2, timestamp_fit, fit2, timestamp_sigma, sigma2 = popt
    timestamp_sigma = abs(timestamp_sigma) # make sure sigma is positive
#    timestamp_x = np.linspace(timestamp_fit-5*timestamp_sigma, timestamp_fit+5*timestamp_sigma, len(bins)*100)
    timestamp_x = np.linspace(0, 250, 1000)

    timestamp_sigma_ps = timestamp_sigma * 1e+3  # convert to ps
    plt.figure(figsize=(10, 8))
    plt.style.use(hep.style.ROOT)

    #plt.hist(timestamp, bins=np.arange(0, 300 + bin_width,bin_width),histtype='stepfilled', edgecolor='black',linewidth = 3.0,alpha=0.6, color='b', label='UFSD-LF')
    plt.hist(timestamp, bins=np.arange(0, 50 + bin_width,bin_width),histtype='stepfilled', edgecolor='black',linewidth = 3.0,alpha=0.6, color='b', label='UFSD-LF')

    plt.plot(timestamp_x, mixed(timestamp_x, timestamp_amp, amp2, timestamp_fit, fit2, timestamp_sigma, sigma2), 'r-',linewidth = 3.0, label = 'mpv = {:.2f} fC \nσ = {:.4f} '.format(timestamp_fit, timestamp_sigma))

    plt.xlim(0, 60)
    plt.ylim(0,100)
    plt.xlabel(r'Charge (fC)')
    plt.ylabel('Counts')
    plt.legend(frameon=False,loc='best',fontsize=18)
    plt.grid()
    # fitting sigma
    # save plt pdf

    plt.savefig(f"{path}/{fname}_collected_charge.png",bbox_inches='tight')
    print("saving fig in the path : ", f"{path}/{fname}_nobin.png")
    plt.clf()

    collected_charge = np.append(collected_charge, timestamp_fit)
    charge_sigma = np.append(charge_sigma, timestamp_sigma)

print("charge:\n", np.array2string(collected_charge, separator=','))
print("sigma:\n", np.array2string(charge_sigma, separator=','))
#print("\nno bin : ", sigma)