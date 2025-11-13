import pyvisa
import time
import sys, os

def Keithely_2470():
    global smu
    ## initialize the keithley 2470 (connected using LXI)
    rm = pyvisa.ResourceManager()
    smu = rm.open_resource('TCPIP0::192.168.0.3')

    # 확인: 장비 연결
    print(smu.query('*IDN?'))  # Check connection

    # 통신 종료 문자 설정
    smu.read_termination = '\n'
    smu.write_termination = '\n'

    # 초기 설정
    smu.write(":SOUR:FUNC VOLT")
    smu.write("SOUR:VOLT:RANG 1000")
    smu.write(":SOUR:VOLT:ILIMIT 500e-6")  # 100uA current limit
    smu.write(":SENS:CURR:RANG 500e-6")
    smu.write(":SENS:FUNC \"VOLT\"")
    smu.write(":SENS:FUNC \"CURR\"")

    # 현재 전압 확인
    current_voltage = int(smu.query("SOUR:VOLT:LEV?"))
    if -1 <= current_voltage <= 1:
        smu.write("SOUR:VOLT:LEV 0")
        print("전압이 ±1V 이내 → 0V로 초기화됨")
    else:
        print(f"현재 전압이 {current_voltage:.2f} V → 초기화하지 않음")

def Keithely_2470_bias_apply(bias):
    """
    Apply a bias voltage to the SMU.
    :param bias: The voltage to apply (in volts).
    """
    smu.write(f"SOUR:VOLT:LEV {bias}")
    smu.write("OUTP ON")
    # check the current
    current = float(smu.query("MEAS:CURR?"))
    print(f"Applied bias voltage: {bias:.2f} V, Current: {current:.2f} A")

def Keithely_2470_increase_10V():
    """
    현재 설정된 전압에서 +10V 증가시켜 다시 설정하고 출력.
    """
    current_voltage = float(smu.query("SOUR:VOLT:LEV?"))
    new_voltage = current_voltage + 10
    smu.write(f"SOUR:VOLT:LEV {new_voltage}")
    smu.write("OUTP ON")
    print(f"전압을 {current_voltage:.2f} V → {new_voltage:.2f} V 로 증가시켰습니다.")

# 실행
Keithely_2470()

# -1V부터 -10V까지 1V씩 감소하면서 출력

current_voltage = int(smu.query("SOUR:VOLT:LEV?"))
target_voltage = int(sys.argv[1])

#if target_voltage < 0:
#    target_voltage = target_voltage 
#elif target_voltage == 0:
#    target_voltage = 1

step = 0
if current_voltage < int(target_voltage):
    step = 5  # 증가
else:
    step = -5
    
if current_voltage > target_voltage:
    # 전압을 내리는 경우
    while current_voltage >= target_voltage:
        Keithely_2470_bias_apply(current_voltage)
        time.sleep(0.1)
        if current_voltage == target_voltage:
            break
        current_voltage += step  # step은 음수여야 함

elif current_voltage < target_voltage:
    # 전압을 올리는 경우
    while current_voltage <= target_voltage:
        Keithely_2470_bias_apply(current_voltage)
        time.sleep(0.1)
        if current_voltage == target_voltage:
            break
        current_voltage += step  # step은 양수여야 함

else:
    # 이미 목표 전압에 도달한 경우
    Keithely_2470_bias_apply(current_voltage)