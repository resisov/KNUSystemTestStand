import numpy as np
import matplotlib.pyplot as plt
import mplhep as hep
from matplotlib.colors import LogNorm  # ← 이거 추가

load = np.load("xy_charge.npy")


# print the length of the 2d array
print("Shape of the loaded array:", load.shape)

# heatmap log scale (min = 1.5625e-05, max = 0.0001)
# logscale
plt.style.use(hep.style.ROOT)
plt.figure(figsize=(8, 8))
plt.imshow((load), cmap='hot', interpolation='nearest')

#plt.imshow(load, cmap='hot', interpolation='nearest', vmin=1.5625e-05, vmax=0.0001)
plt.colorbar()

#plt.title("Pulse Peak Heatmap")
plt.xlabel("X Axis")
plt.ylabel("Y Axis")
#plt.savefig('xy_charge_heatmap.png')
plt.show()