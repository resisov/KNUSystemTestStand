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
# Define a Gaussian function for fitting

def gaussian(x, amp, mean, sigma):
    return amp * np.exp(-((x - mean) ** 2) / (2 * sigma ** 2))

# find the files in the path and sort them by voltage
#files = glob.glob('output/LF_W2_LGAD_PreIrrad_Width81p2/*.root')
#files = glob.glob('output/LF_W1_LGAD_1p0e15_Width81p2/*.root')
files = glob.glob('output/K1_1x1_LGAD_laserwidth81p15/*.root')
#files = glob.glob('output/LF_W7_LGAD_5p0e15_Width81p2/*.root')

voltages = []
for path in files:
    match = re.search(r'_(\d+)\.root$', path)
    if match:
        voltages.append(int(match.group(1)))
    else:
        print(f"⚠️ 파일명에서 전압 못 찾음: {path}")

voltages = np.array(voltages)
files = np.array(files)

sorted_indices = np.argsort(voltages)
voltages_sorted = voltages[sorted_indices].tolist()
files_sorted = files[sorted_indices].tolist()
files_reduced = str(files_sorted[0].split('/')[2].split('.')[0])
print(files_reduced)

# array for selected data
x_sel = np.array([]) # x values for the selected data
y_sel = np.array([]) # y values for the selected data

res = np.array([]) # sigma calculated using binned gaussian fit
for j in range(len(voltages_sorted)): # file loop

    data = uproot.open(files_sorted[j])
    fname = str(files_sorted[j].split('/')[2].split('.')[0])

    print(files_sorted[j])
    time = data["Events"]["time"].array()
    waveform = -data['Events']['ch2'].array()

    # reset array
    peak_voltages = np.array([])
    timestamp = np.array([])
    timestamp_nobin = np.array([])
    for i in range(len(waveform)): # event loop

        x = np.array(time[i])
        y = np.array(waveform[i])

        ped_mean = np.mean(y[:400])
        y = y - ped_mean
        peak_index = np.argmax(np.abs(y))
        peak_value = y[peak_index]
        peak_time = x[peak_index]
        if (peak_time) < 7e-9 or (peak_time) > 1.3e-8:
            #print(f'Skipping event {i} due to peak time out of range: {peak_time}')
            continue        
        peak_voltage = np.max(y)
        matching_indices = ak.where(y < 0)[0]

        before = np.max(matching_indices[matching_indices <  peak_index])  # Find the maximum index before the peak index
        after = np.min(matching_indices[matching_indices > peak_index])  # Find the minimum index after the peak index

        # if before or after is none skip this event
        if before is None or after is None or before >= after:
            #print(f'Skipping event {i} due to invalid indices before or after peak.')
            timestamp = np.append(timestamp, -99.0)
            continue

        before = before + 1
        after = after - 1

        try:
            fit_x = np.asarray(x[before:after]) # fitting range
            step = (fit_x[1] - fit_x[0])/50. # 1ps bin
            fit_x_new = np.arange(fit_x[0], fit_x[-1]+ step, step) # increase step of fitting
            fit_y = np.asarray(y[before:after])
            popt, _ = curve_fit(gaussian, fit_x, fit_y, p0=[peak_voltage, peak_time, 1e-9], maxfev=10000)
            fit_amp, fit_mean, fit_sigma = popt

            fit_curve = gaussian(fit_x_new, fit_amp, fit_mean, fit_sigma)
            threshold = 0.2 * fit_amp
            idx_rise = np.where((fit_curve >= threshold) & (fit_x_new <= fit_mean))[0] # find the indexs (from 20% ~ mean of the gaussian)

            if len(idx_rise) > 0: # if the index is found
                t_20 = (fit_mean - abs(fit_sigma) * 1.794) * 1e+9
                #print(t_20)
                timestamp = np.append(timestamp,t_20)
                y_sel = y

            else:
                #print(f'No valid TOA index found for channel 2 and event {i}. Skipping fit. case2')
                timestamp = np.append(timestamp, -99.0)

        except:
            #print(f'Fit failed for channel 2 and event {i}. Skipping fit. case1')
            timestamp = np.append(timestamp, -99.0)  # Placeholder for failed fit

        #plt.plot(x, y_sel)
        #plt.xlabel('Time [ns]')
        #plt.ylabel('Voltage [V]')
        #plt.title(f"Waveform of {fname}")

        #counts, bins = np.histogram(timestamp_nobin, bins = np.arange(7, 13.05,0.05))


        #plt.savefig(f"time_plot/{i}_waveform.png")
        #plt.clf()



    # masking failed events
    mask = timestamp != -99.0
    timestamp = timestamp[mask]

    timestamp = timestamp

    mu = np.mean(timestamp)
    std = np.std(timestamp)

    print(mu, std)

    mask = (timestamp < (mu + 3 * std)) & (timestamp > (mu - 3 * std))
    timestamp = timestamp[mask]

    # histogram 계산만

    bin_width = 0.03
    counts, bins = np.histogram(timestamp, bins=np.arange(8,11 + bin_width,bin_width))
    bin_center = (bins[:-1] + bins[1:]) / 2

    # Plotting the histogram
    plt.figure(figsize=(10, 6))
    plt.title('Timestamp (fittied) Distribution')
    plt.xlabel('Timestamp [ns]')
    plt.ylabel('Count')
    plt.hist(timestamp, bins=bins, alpha=0.6, color='g', label='Data Histogram')
    # Plotting the fitted Gaussian

    timestamp_x = np.linspace(8, 11, len(bins)*100)
    p0 = [max(counts), mu, std]
    bounds = ([0, -np.inf, 1e-12], [np.inf, np.inf, np.inf])
    popt, _ = curve_fit(gaussian, bin_center, counts, p0=p0,bounds=bounds, maxfev=10000) # fitting
    A, mean, sigma = popt

    print(A,mean,sigma)
    # text the fitted mean and standard deviation

    plt.plot(timestamp_x, gaussian(timestamp_x, A, mean, sigma),
         'r-', linewidth=3.0,
         label = r'$\mu={:.2f}\ \mathrm{{ns}}$' '\n' r'$\sigma={:.4f}\ \mathrm{{ns}}$'.format(mean, sigma))

    ############################################################################################################
    # save distribution of timestamp with no bin
    plt.xlim(mean - 5*sigma, mean + 5*sigma)
    #plt.title('Timestamp (no bin) Distribution')
    plt.xlabel(r'$t_{20\%}$ (ns)')
    plt.ylabel('Counts')
    plt.legend(frameon=False,loc='upper left',fontsize=18)
    plt.grid()
    # save plt pdf
    plt.savefig(f"output/K1_1x1_LGAD_laserwidth81p15/{fname}_nobin.png",bbox_inches='tight')
    plt.clf()

    sigma = sigma * 1e+3 # convert to ps
    res = np.append(res, sigma)

print("no bin:", np.array2string(res, separator=', '))

