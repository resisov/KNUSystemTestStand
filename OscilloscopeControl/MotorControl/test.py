import libximc.highlevel._highlevel as hh

ports = ["/dev/ttyACM0", "/dev/ttyACM1", "/dev/ttyACM2"]

for p in ports:
    uri = f"xi-com:{p}"
    print(f"Trying {uri} ...")
    try:
        dev = hh.lib.open_device(uri.encode())
        print(f"\n🎉 SUCCESS! Motor found at {p}")
        
    except Exception:
        print(f"FAIL on {p}")
