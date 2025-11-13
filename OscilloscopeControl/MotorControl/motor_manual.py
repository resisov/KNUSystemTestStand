import pathlib
import libximc.highlevel as ximc
import os, sys
import pyvisa
import time
import numpy as np
import uproot
import argparse
import awkward as ak
import utils.artwork as artwork
import matplotlib.pyplot as plt
import mplhep as hep



# Device URI
device_uri3 = "xi-com:/dev/ttyACM0"  # Y
device_uri2 = "xi-com:/dev/ttyACM1"  # X
device_uri1 = "xi-com:/dev/ttyACM2"  # Z
# Axis 객체
z_axis = ximc.Axis(device_uri1)
x_axis = ximc.Axis(device_uri2)
y_axis = ximc.Axis(device_uri3)
# Device 열기
z_axis.open_device() # if code fails here, try "sudo -E python motor_manual.py" (it will get sudo permission with current environment)
x_axis.open_device()
y_axis.open_device()
# 위치 0으로 설정
x_axis.command_zero()
y_axis.command_zero()
z_axis.command_zero()

# get the x and y moving value from keybaord
x_move = int(input("Enter the x moving value: ")) # plus move the plate to the right (laser point move to the left)
y_move = int(input("Enter the y moving value: ")) # plus move the plate down (laser point move to the up)

# move 8step to the right
x_axis.command_move(-x_move,0)
x_axis.command_wait_for_stop(10)  # wait for the motor to stop
y_axis.command_move(y_move,0)
y_axis.command_wait_for_stop(10)  # wait for the motor to stop

# Device 닫기
x_axis.close_device()
y_axis.close_device()
z_axis.close_device()
# End     print    end_time = time.time()