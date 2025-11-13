import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
from scipy.special import erf

# erf difference model
def erf_diff(y, A, y1, y2, sigma, B):
    return A * (erf((y - y1) / (np.sqrt(2) * sigma)) - erf((y - y2) / (np.sqrt(2) * sigma))) + B

# 예시 데이터
y = np.linspace(0, 300, 300)
charge = erf_diff(y, -80, 90, 160, 10, 0) + np.random.normal(0, 1, len(y))  # synthetic data

# Fit
popt, _ = curve_fit(erf_diff, y, charge, p0=[-80, 90, 160, 10, 0])

# FWHM 계산
fwhm = abs(popt[2] - popt[1])
print(f"FWHM: {fwhm:.2f} μm")

# 시각화
plt.plot(y, charge, label='data')
plt.plot(y, erf_diff(y, *popt), label='fit', color='red')
plt.xlabel('Y position [μm]')
plt.ylabel('Charge [arb.]')
plt.legend()
plt.title(f'FWHM: {fwhm:.2f} μm')
plt.grid()
plt.show()
