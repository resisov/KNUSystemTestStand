import pyvisa
import time
import sys, os

class Keithley:
    def __init__(self):
        self.rm = pyvisa.ResourceManager()
        self.smu = self.rm.open_resource('TCPIP0::192.168.0.3')
        ## Confirm connection
        print(self.smu.query('*IDN?'))
        ## Set termination characters
        self.smu.read_termination = '\n'
        self.smu.write_termination = '\n'
        ## Initial settings
        self.smu.write(":SOUR:FUNC VOLT")
        self.smu.write("SOUR:VOLT:RANG 1000")
        self.smu.write(":SOUR:VOLT:ILIMIT 500e-6")
        self.smu.write(":SENS:CURR:RANG 500e-6")
        self.smu.write(":SENS:FUNC \"VOLT\"")
        self.smu.write(":SENS:FUNC \"CURR\"")
    
    def reset_voltage(self):
        # read the current voltage level
        current_voltage = int(self.smu.query("SOUR:VOLT:LEV?"))
        # reset to 0V with 10V step
        if current_voltage > 0:
            # decrease voltage in steps of 10V until it reaches 0V
            while True:
                self.smu.write(f"SOUR:VOLT:LEV {current_voltage - 10}")
                current_voltage -= 10
                time.sleep(0.5)
                if current_voltage <= 10:
                    self.smu.write("SOUR:VOLT:LEV 0")
                    print("Voltage reset to 0V")
                    break
        elif current_voltage < 0:
            # increase voltage in steps of 10V until it reaches 0V
            while True:
                self.smu.write(f"SOUR:VOLT:LEV {current_voltage + 10}")
                current_voltage += 10
                time.sleep(0.5)
                if current_voltage >= -10:
                    self.smu.write("SOUR:VOLT:LEV 0")
                    print("Voltage reset to 0V")
                    break
        else:
            print("Current voltage is already 0V, no reset needed.")
        
    def adjust_voltage(self, step):
        """
        Adjust the voltage by a specified step.
        :param step: The step to adjust the voltage by (in volts).
        """
        current_voltage = int(self.smu.query("SOUR:VOLT:LEV?"))
        new_voltage = current_voltage + step
        self.smu.write(f"SOUR:VOLT:LEV {new_voltage}")
        self.smu.write("OUTP ON")
        print(f"Adjusted voltage from {current_voltage:.2f} V to {new_voltage:.2f} V")

    def apply_voltage(self, target_voltage):
        """
        Apply a bias voltage to the SMU.
        :param target_voltage: The voltage to apply (in volts).
        """
        self.reset_voltage()
        self.smu.write("OUTP ON")
        if abs(target_voltage) > 20:
            # increase gradually if target voltage is more than 50V
            current_voltage = int(self.smu.query("SOUR:VOLT:LEV?"))
            if target_voltage > current_voltage:
                step = 10
            else:
                step = -10
            while abs(current_voltage - target_voltage) > 1:
                current_voltage += step
                self.smu.write(f"SOUR:VOLT:LEV {current_voltage}")
                time.sleep(0.5)
                print(f"Current voltage: {current_voltage:.2f} V")
            target_voltage = current_voltage  # Set to the last adjusted voltage

        self.smu.write(f"SOUR:VOLT:LEV {target_voltage}")
        
        print(f"Applied bias voltage: {target_voltage:.2f} V")
    
    def test_sequence(self, target_voltage):
        """
        Test sequence to apply a voltage and then adjust it.
        :param target_voltage: The voltage to apply (in volts).
        """
        self.apply_voltage(target_voltage)
        time.sleep(1)
        # Adjust voltage by -10V
        for i in range(20):
            self.adjust_voltage(-10)
            time.sleep(0.5)
        self.reset_voltage()

if __name__ == "__main__":
    keithley = Keithley()
    # Reset voltage to 0V
    keithley.reset_voltage()
    
    # Apply a target voltage (e.g., -10V)
    target_voltage = -10  # Change this value as needed
    keithley.test_sequence(target_voltage)
    
    # Adjust voltage by +10V
    keithley.reset_voltage()
    
    # Close the resource manager
    keithley.smu.close()
    keithley.rm.close()
