import libximc.highlevel as ximc

axis = ximc.Axis("xi-com:/dev/ttyACM0")
axis.open_device()

info = axis.get_device_information()

print("Manufacturer :", info.Manufacturer)
print("Product      :", info.ProductDescription)

if hasattr(info, "SerialNumber"):
    print("Serial      :", info.SerialNumber)

if hasattr(info, "FirmwareVersion"):
    print("Firmware    :", info.FirmwareVersion)

if hasattr(info, "HardwareVersion"):
    print("Hardware    :", info.HardwareVersion)

engine = axis.get_engine_settings()
print(engine.StepsPerRev)
print(engine.MicrostepMode)
