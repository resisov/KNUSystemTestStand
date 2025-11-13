# visa_test_resilient.py
import pyvisa

IP = "192.168.100.100"
ADDR = f"TCPIP0::{IP}::INSTR"

def q(inst, cmd):
    try:
        return inst.query(cmd).strip()
    except Exception as e:
        return f"[fail] {type(e).__name__}: {e}"

def try_cmds(inst, label, cmds):
    for c in cmds:
        r = q(inst, c)
        if not r.startswith("[fail]"):
            print(f"{label}: {c} -> {r}")
            return r, c
        # 일부 미지원 명령은 타임아웃 대신 에러큐만 쌓일 수 있음
    print(f"{label}: all failed ({', '.join(cmds)})")
    return None, None

def main():
    rm = pyvisa.ResourceManager()
    inst = rm.open_resource(ADDR)
    inst.write_termination = '\n'
    inst.read_termination  = '\n'
    inst.timeout = 8000  # ms

    # 응답 포맷(헤더) 정리
    for cmd in ("CHDR OFF", "COMM_HEADER OFF"):
        try:
            inst.write(cmd)
            break
        except Exception:
            pass

    print("*IDN? ->", q(inst, "*IDN?"))

    # 표준 상태 / 동작 완료 비트
    print("*ESR? ->", q(inst, "*ESR?"))  # Standard Event Status Register
    print("*STB? ->", q(inst, "*STB?"))  # Status Byte
    print("*OPC? ->", q(inst, "*OPC?"))  # Operation Complete (1 기대)

    # 에러 큐: SYST:ERR? 가 아니고 LERR? 를 쓰는 경우가 많음
    try_cmds(inst, "Error", ["SYST:ERR?", "LERR?"])

    # Alive/Health 대체: 일부 FW에서 ALIV? 미지원
    try_cmds(inst, "Alive", ["ALIV?", "BUSY?", "TRIG_STATE?"])

    # 채널 파라미터
    for cmd in ["C1:VDIV?", "C1:OFST?", "C1:COUPLING?", "C1:TRACE?"]:
        print(f"{cmd} ->", q(inst, cmd))

    inst.close()
    print("Done.")

if __name__ == "__main__":
    main()