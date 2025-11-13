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

#print("sorted voltages = ", voltages_sorted)
#print("sorted files list = ", files_sorted)
# file sort end

#files_sorted = np.array(["output/LF_W2_LGAD_PreIrrad_Width81p2/waveforms_scan_230.root","output/LF_W1_LGAD_1p0e15_Width81p2/waveforms_scan_420.root","output/LF_W1_LGAD_1p5e15_Width81p2/waveforms_scan_550.root","output/LF_W7_LGAD_5p0e15_Width81p2/waveforms_scan_590.root"])
#voltages_sorted = np.array(["230","420","550","590"])
#wafer_index = np.array(["Wafer2","Wafer1","Wafer1","Wafer7"])
#irrad_index = np.array(['Pre-Irrad','1.0e+15 $n_{eq}/cm^{2}$','1.5e+15 $n_{eq}/cm^{2}$','5.0e+15 $n_{eq}/cm^{2}$'])
#bin_width = np.array([0.01, 0.01, 0.02, 0.02]) # bin width for the histogram
files_reduced = str(files_sorted[0].split('/')[2].split('.')[0])
print(files_reduced)

# array for selected data
x_sel = np.array([]) # x values for the selected data
y_sel = np.array([]) # y values for the selected data

sigma = np.array([]) # sigma calculated using binned gaussian fit
sigma_nobin = np.array([]) # sigma calculated using formula
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
                toa_index = idx_rise[0] # take the first index
                timestamp = np.append(timestamp, fit_x_new[toa_index])
                t_20 = (fit_mean - abs(fit_sigma) * 1.794) * 1e+9
                #print(t_20)
                timestamp_nobin = np.append(timestamp_nobin,t_20)
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

    timestamp = timestamp * 1e+9

    mu = np.mean(timestamp)
    std = np.std(timestamp)

    mask = (timestamp < (mu + 3 * std)) & (timestamp > (mu - 3 * std))
    timestamp = timestamp[mask]

    # histogram 계산만
    counts, bins = np.histogram(timestamp, bins=np.arange(9,11.025,0.025))
    bin_center = (bins[:-1] + bins[1:]) / 2

    # Plotting the histogram
    plt.figure(figsize=(10, 6))
    plt.title('Timestamp (fittied) Distribution')
    plt.xlabel('Timestamp [ns]')
    plt.ylabel('Count')
    plt.hist(timestamp, bins=bins, alpha=0.6, color='g', label='Data Histogram')
    plt.clf()
    # Plotting the fitted Gaussian
    xmin, xmax = plt.xlim()

    timestamp_x = np.linspace(8, 15, len(bins)*100)
    p0 = [30, 8.5, std]
    bounds = ([0, -np.inf, 1e-12], [np.inf, np.inf, np.inf])
    popt, _ = curve_fit(gaussian, bin_center, counts, p0=p0,bounds=bounds, maxfev=10000) # fitting
    timestamp_amp, timestamp_fit, timestamp_sigma = popt

    # text the fitted mean and standard deviation
    fitting = np.linspace(9, 11, len(bins)*100)

    ############################################################################################################
    # save distribution of timestamp with no bin

    bin_width = 0.2
    mu_init = np.mean(timestamp_nobin)
    std_init = np.std(timestamp_nobin)

    counts, bins = np.histogram(timestamp_nobin,
                                bins=np.arange(mu_init-5*std_init, mu_init+5*std_init+bin_width, bin_width))
    bin_center = 0.5*(bins[:-1] + bins[1:])
    p0 = [max(counts), mu_init, max(std_init, bin_width/2)]

    # bounds는 완화
    bounds = ([0.0, -np.inf, 0.0], [np.inf, np.inf, np.inf])

    popt, _ = curve_fit(gaussian, bin_center, counts, p0=p0, bounds=bounds, maxfev=20000)
    A_fit, mu_fit, sigma_fit = popt

    # 피팅 후 범위/샘플 재생성
    timestamp_nobin_x = np.linspace(mu_fit - 5*sigma_fit, mu_fit + 5*sigma_fit, 2000)

    # 히스토그램과 피팅 스케일 일치
    w_fit  = bin_width
    w_plot = bin_width  # 실제로 다른 값을 쓰면 여기만 바꾸면 됨
    scale  = w_plot / w_fit

    plt.hist(timestamp_nobin,
            bins=np.arange(mu_fit-5*sigma_fit, mu_fit+5*sigma_fit+w_plot, w_plot),
            histtype='stepfilled', edgecolor='black', linewidth=3.0, alpha=0.6, color='b',
            label='UFSD-LF Wafer 2 LGAD')

    plt.plot(timestamp_nobin_x, scale*gaussian(timestamp_nobin_x, A_fit, mu_fit, sigma_fit),
         'r-', linewidth=3.0,
         label = r'$\mu={:.2f}\ \mathrm{{ns}}$' '\n' r'$\sigma={:.4f}\ \mathrm{{ns}}$'.format(mu_fit, sigma_fit))


    #plt.text(0.9,0.8,"")
    plt.xlim(mu-5*std-0.05, mu+5*std)
    #plt.title('Timestamp (no bin) Distribution')
    plt.xlabel(r'$t_{20\%}$ (ns)')
    plt.ylabel('Counts')
    plt.legend(frameon=False,loc='upper left',fontsize=18)
    plt.grid()
    # fitting sigma_nobin
    # save plt pdf
    plt.savefig(f"output/{fname}_nobin.png",bbox_inches='tight')
    plt.clf()

    sigma_fit = sigma_fit * 1e+3 # convert to ps

    sigma_nobin = np.append(sigma_nobin, sigma_fit)

print("no bin:", np.array2string(sigma_nobin, separator=', '))
#print("\nno bin : ", sigma_nobin)

#histo = plt.hist(charge, range=(mean-3*std, mean+12*std), bins=150 ,histtype='stepfilled', edgecolor='black', color = '#3D74B6', linewidth=2, label='$\mathbf{UFSD-LF}$ $\mathbf{'+wafer_index+'}$ $\mathbf{LGAD}$'+"\nLaser Width @ 81.2%\nBias Voltage: "+str(file.split('_')[-1].replace('.root', ''))+"V\n"+irrad_index)
#plt.plot(x, gaussian(x, *sopt), '-', label='$\mathbf{Gaussian Fit}$\n'+r'$\mu=%.2f$' % sopt[1]+'\n'+r'$\sigma=%.2f$' % abs(sopt[2]), linewidth=3, color='#DC3C22')
