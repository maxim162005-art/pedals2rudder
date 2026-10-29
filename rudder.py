# -*- coding: utf-8 -*-
"""
pedals2rudder — use two racing pedals (gas + brake) as flight-sim rudder pedals.

Left pedal  -> rudder left      (vJoy axis X)
Right pedal -> rudder right     (vJoy axis X)
BOTH pedals -> wheel brakes     (vJoy axes Y and Z = left / right toe brake)

Brake strength = how far the LESS pressed pedal is down. A difference between
the pedals of up to `brake_tol` (30 %) counts as "both together" and does not
move the rudder, so you can brake straight without fighting the yaw.

First run = setup: the program asks you to press each pedal and remembers
which axis is which. After that just run it and keep the window open while
you fly. Ctrl+C or closing the window stops it and centres the rudder.

    python rudder.py              run (does setup on first start)
    python rudder.py --setup      choose the pedals / axes again
    python rudder.py --calibrate  re-measure the vJoy axis mapping only
    python rudder.py --check      list devices, test vJoy, exit

Requires: Windows, Python 3.9+, pygame-ce, vJoy driver with Device 1 enabled
(axes X, Y, Z).  https://github.com/BrunnerInnovation/vJoy/releases
"""
import os
import sys
import json
import time
import ctypes

# ---- defaults (saved per machine in rudder_config.json after setup) -------
VJOY_ID     = 1          # vJoy device number
DEADZONE    = 0.04       # dead zone at the released pedal, 4 %
RATE_HZ     = 100        # update rate
HID_USAGE_X = 0x30       # rudder
HID_USAGE_Y = 0x31       # left toe brake
HID_USAGE_Z = 0x32       # right toe brake
AXIS_MAX    = 32768
BRAKE_MIN   = 0.15       # both pedals >= 15 % -> braking
BRAKE_TOL   = 0.30       # difference up to 30 % = "together", no rudder
# Raw vJoy values that Windows reports as -1 / 0 / +1. Nominal is 0/16384/32768,
# but a per-device calibration in Windows "Game Controllers" can skew it;
# setup measures the real values automatically (see calibrate_vjoy).
VJOY_DEFAULT = {"lo": 0, "center": 16384, "hi": 32768}
# ---------------------------------------------------------------------------

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_JOYSTICK_ALLOW_BACKGROUND_EVENTS"] = "1"
os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

try:
    import pygame  # noqa: E402
except ImportError:
    print("pygame-ce is not installed. Run:   pip install pygame-ce")
    sys.exit(1)

HERE = os.path.dirname(os.path.abspath(__file__))
CFG = os.path.join(HERE, "rudder_config.json")


def die(msg):
    print("\n" + "=" * 60)
    print("ERROR")
    print(msg)
    print("=" * 60)
    sys.exit(1)


# ---- pure maths (unit-tested in tests/test_mix.py) -------------------------
def to_raw(rudder, vjoy=VJOY_DEFAULT):
    """-1..+1 -> raw vJoy axis value, honouring a skewed centre."""
    rudder = max(-1.0, min(1.0, rudder))
    lo, c, hi = vjoy["lo"], vjoy["center"], vjoy["hi"]
    if rudder >= 0:
        return int(round(c + rudder * (hi - c)))
    return int(round(c + rudder * (c - lo)))


def mix(l, r, brake_min=BRAKE_MIN, tol=BRAKE_TOL):
    """l, r = pedal travel 0..1.  Returns (rudder -1..+1, brake 0..1).

    One pedal          -> rudder towards it, no brake.
    Both >= brake_min  -> brake = common part (the less pressed pedal);
                          rudder = difference beyond `tol`, otherwise 0.
    """
    common = min(l, r)
    diff = r - l
    if common >= brake_min:
        brake = (common - brake_min) / (1.0 - brake_min)
        if abs(diff) <= tol:
            rudder = 0.0
        else:
            rudder = (abs(diff) - tol) / (1.0 - tol)
            rudder = rudder if diff > 0 else -rudder
        return rudder, brake
    return diff, 0.0


def norm(v, c, dz):
    """Raw axis value -> 0..1 travel using the rest/pressed points from setup."""
    span = c["pressed"] - c["rest"]
    t = (v - c["rest"]) / span if abs(span) > 1e-6 else 0.0
    t = max(0.0, min(1.0, t))
    if t < dz:
        return 0.0
    return (t - dz) / (1.0 - dz)


# ---- vJoy via ctypes --------------------------------------------------------
def vjoy_dll_path():
    bits = ctypes.sizeof(ctypes.c_void_p) * 8
    sub = "x64" if bits == 64 else "x86"
    for base in (os.environ.get("ProgramFiles", r"C:\Program Files"),
                 os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")):
        p = os.path.join(base, "vJoy", sub, "vJoyInterface.dll")
        if os.path.exists(p):
            return p
    return None


def open_vjoy():
    dll = vjoy_dll_path()
    if not dll:
        die("vJoyInterface.dll not found. Install vJoy:\n"
            "  https://github.com/BrunnerInnovation/vJoy/releases")
    vj = ctypes.WinDLL(dll)
    vj.vJoyEnabled.restype = ctypes.c_bool
    vj.GetVJDStatus.restype = ctypes.c_int
    vj.GetVJDStatus.argtypes = [ctypes.c_uint]
    vj.AcquireVJD.restype = ctypes.c_bool
    vj.AcquireVJD.argtypes = [ctypes.c_uint]
    vj.RelinquishVJD.argtypes = [ctypes.c_uint]
    vj.SetAxis.restype = ctypes.c_bool
    vj.SetAxis.argtypes = [ctypes.c_long, ctypes.c_uint, ctypes.c_uint]

    if not vj.vJoyEnabled():
        die("The vJoy driver is not running. Reboot or reinstall vJoy.")
    st = vj.GetVJDStatus(VJOY_ID)       # 0 own, 1 free, 2 busy, 3 missing
    if st == 2:
        die("vJoy Device %d is in use by another program.\n"
            "Close Joystick Gremlin / another copy of this program." % VJOY_ID)
    if st == 3:
        die("vJoy Device %d does not exist.\n"
            "Open 'Configure vJoy', enable Device %d with axes X, Y, Z, click Apply."
            % (VJOY_ID, VJOY_ID))
    if not vj.AcquireVJD(VJOY_ID):
        die("Could not acquire vJoy Device %d." % VJOY_ID)
    return vj


# ---- devices ---------------------------------------------------------------
def clean_name(s):
    """Device name without garbage bytes (SDL sometimes appends e.g. \\x90)."""
    return "".join(ch for ch in s if ch.isprintable()).strip()


def is_vjoy(j):
    return "VJOY" in clean_name(j.get_name()).upper()


def list_devices():
    pygame.init()
    pygame.joystick.init()
    return [pygame.joystick.Joystick(i) for i in range(pygame.joystick.get_count())]


def read_all(j):
    pygame.event.pump()
    return [j.get_axis(k) for k in range(j.get_numaxes())]


def choose_device(devs, saved_name=None):
    """Return the pedal device: by saved name, else the only real device, else ask."""
    real = [j for j in devs if not is_vjoy(j)]
    if saved_name:
        for j in real:
            if clean_name(j.get_name()) == clean_name(saved_name):
                return j
    if not real:
        die("No game controller found (only vJoy or nothing).\n"
            "Is the pedal base powered and plugged into USB?")
    if len(real) == 1:
        return real[0]
    print()
    print("Several controllers found. Which one are the PEDALS?")
    for i, j in enumerate(real):
        print("  [%d] %s   (%d axes)" % (i, clean_name(j.get_name()), j.get_numaxes()))
    while True:
        s = input("Number > ").strip()
        if s.isdigit() and int(s) < len(real):
            return real[int(s)]


def pick_axis(j, label, rest):
    input("   Press and HOLD the pedal for rudder %s, then press Enter > " % label)
    pressed = read_all(j)
    deltas = [abs(pressed[k] - rest[k]) for k in range(len(rest))]
    k = max(range(len(deltas)), key=lambda i: deltas[i])
    if deltas[k] < 0.3:
        die("No pedal movement seen. Press fully and keep holding until you press Enter.\n\n"
            "If you did hold it, the pedals are not reaching the PC:\n"
            "  - check the pedal cable into the wheel base / USB adapter;\n"
            "  - open the manufacturer's software: do the bars move there?\n"
            "    No = hardware/cable.  Yes = close that software and retry.\n"
            "Axes now: " + " ".join("%d=%+.2f" % (i, v) for i, v in enumerate(pressed)))
    input("   Release the pedal, then press Enter > ")
    return {"axis": k, "rest": rest[k], "pressed": pressed[k]}


# ---- vJoy self-calibration --------------------------------------------------
def calibrate_vjoy(vj, devs, verbose=True):
    """Write known raw values to vJoy and read them back through the joystick API.

    Finds the raw values Windows maps to -1, 0 and +1. If the vJoy device is
    not visible (e.g. hidden by HidHide) the nominal mapping is returned.
    """
    vdev = next((j for j in devs if is_vjoy(j)), None)
    if vdev is None:
        if verbose:
            print("vJoy device not visible to the joystick API; using nominal mapping.")
        return dict(VJOY_DEFAULT)

    def read(raw):
        vj.SetAxis(raw, VJOY_ID, HID_USAGE_X)
        time.sleep(0.03)
        for _ in range(4):
            pygame.event.pump()
            time.sleep(0.01)
        return vdev.get_axis(0)

    # sanity: must be monotonic and actually move
    lo_v, hi_v = read(0), read(AXIS_MAX)
    if not (lo_v < -0.9 and hi_v > 0.9):
        if verbose:
            print("vJoy axis X does not respond as expected (%+.2f .. %+.2f); using nominal mapping."
                  % (lo_v, hi_v))
        return dict(VJOY_DEFAULT)

    def search(target, lo, hi):
        # binary search for raw value whose reading is closest to target
        while hi - lo > 1:
            mid = (lo + hi) // 2
            if read(mid) < target:
                lo = mid
            else:
                hi = mid
        return hi

    center = search(0.0, 0, AXIS_MAX)
    lo = search(-0.999, 0, center)
    hi = search(0.999, center, AXIS_MAX)
    vj.SetAxis(center, VJOY_ID, HID_USAGE_X)
    m = {"lo": lo, "center": center, "hi": hi}
    if verbose:
        print("vJoy mapping measured: -1 = %d, 0 = %d, +1 = %d" % (lo, center, hi))
        if abs(center - VJOY_DEFAULT["center"]) > 300:
            print("  (centre is offset from nominal; Windows has a calibration for the vJoy "
                  "device. That's fine, it is compensated.)")
    return m


# ---- setup / config --------------------------------------------------------
def setup(j, vj, devs):
    print()
    print("SETUP.  Device: " + clean_name(j.get_name()))
    print()
    input("1. Release BOTH pedals, don't touch anything, press Enter > ")
    rest = read_all(j)
    print()
    left = pick_axis(j, "LEFT (left pedal)", rest)
    print()
    right = pick_axis(j, "RIGHT (right pedal)", rest)
    if left["axis"] == right["axis"]:
        die("Both pedals gave the same axis. Run setup again and press different pedals.")
    print()
    print("Measuring vJoy axis mapping...")
    vjoy = calibrate_vjoy(vj, devs)
    cfg = {"device": clean_name(j.get_name()), "left": left, "right": right,
           "invert": False, "deadzone": DEADZONE,
           "brake_min": BRAKE_MIN, "brake_tol": BRAKE_TOL, "vjoy": vjoy}
    save_cfg(cfg)
    print()
    print("Done. Left = axis %d, right = axis %d. Saved to rudder_config.json"
          % (left["axis"], right["axis"]))
    print('If the sides turn out swapped, open rudder_config.json and set "invert": true')
    print()
    return cfg


def save_cfg(cfg):
    with open(CFG, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)


def load_cfg():
    with open(CFG, encoding="utf-8") as f:
        return json.load(f)


# ---- main loop -------------------------------------------------------------
def bar(x, width=21):
    pos = int(round((x + 1) / 2 * (width - 1)))
    cells = ["-"] * width
    cells[width // 2] = "|"
    cells[pos] = "O"
    return "[" + "".join(cells) + "]"


def run(j, vj, cfg):
    L, R = cfg["left"], cfg["right"]
    dz = cfg.get("deadzone", DEADZONE)
    sign = -1.0 if cfg.get("invert") else 1.0
    period = 1.0 / RATE_HZ
    bmin = cfg.get("brake_min", BRAKE_MIN)
    btol = cfg.get("brake_tol", BRAKE_TOL)
    vjoy = cfg.get("vjoy", VJOY_DEFAULT)
    print("RUDDER AND BRAKES ACTIVE.  Keep this window open while flying.  Ctrl+C = stop.")
    print("Left = axis %d, right = axis %d, dead zone %d %%"
          % (L["axis"], R["axis"], int(dz * 100)))
    print("Both pedals >= %d %% = braking; difference up to %d %% does not move the rudder"
          % (int(bmin * 100), int(btol * 100)))
    print()
    last = 0.0
    try:
        while True:
            pygame.event.pump()
            l = norm(j.get_axis(L["axis"]), L, dz)
            r = norm(j.get_axis(R["axis"]), R, dz)
            rudder, brake = mix(l, r, bmin, btol)
            rudder *= sign
            braw = int(round(brake * AXIS_MAX))
            vj.SetAxis(to_raw(rudder, vjoy), VJOY_ID, HID_USAGE_X)
            vj.SetAxis(braw, VJOY_ID, HID_USAGE_Y)
            vj.SetAxis(braw, VJOY_ID, HID_USAGE_Z)
            now = time.time()
            if now - last > 0.2:
                n = int(round(brake * 10))
                print("\r  pedals L %3d%% R %3d%%   rudder " % (int(l * 100), int(r * 100))
                      + bar(rudder) + " %+5.2f   brake [%s] %3d%%   "
                      % (rudder, "#" * n + "." * (10 - n), int(brake * 100)),
                      end="", flush=True)
                last = now
            time.sleep(period)
    except KeyboardInterrupt:
        pass
    finally:
        vj.SetAxis(vjoy["center"], VJOY_ID, HID_USAGE_X)
        vj.SetAxis(0, VJOY_ID, HID_USAGE_Y)
        vj.SetAxis(0, VJOY_ID, HID_USAGE_Z)
        vj.RelinquishVJD(VJOY_ID)
        print("\n\nStopped. Rudder centred, brakes released.")


def main():
    args = set(a.lower() for a in sys.argv[1:])
    devs = list_devices()

    if "--check" in args:
        print("Controllers:")
        for i, j in enumerate(devs):
            print("  [%d] %s   axes=%d%s" % (i, clean_name(j.get_name()), j.get_numaxes(),
                                             "   <- vJoy" if is_vjoy(j) else ""))
        vj = open_vjoy()
        vj.RelinquishVJD(VJOY_ID)
        print("vJoy Device %d: OK" % VJOY_ID)
        print("Config: " + ("found" if os.path.exists(CFG) else "none, setup will run on start"))
        return

    vj = open_vjoy()

    if "--calibrate" in args:
        if not os.path.exists(CFG):
            die("No config yet. Run without flags first (setup).")
        cfg = load_cfg()
        cfg["vjoy"] = calibrate_vjoy(vj, devs)
        save_cfg(cfg)
        vj.RelinquishVJD(VJOY_ID)
        print("Saved.")
        return

    if "--setup" in args or not os.path.exists(CFG):
        j = choose_device(devs)
        cfg = setup(j, vj, devs)
    else:
        cfg = load_cfg()
        real = [x for x in devs if not is_vjoy(x)]
        match = [x for x in real if clean_name(x.get_name()) == clean_name(cfg.get("device", ""))]
        if match:
            j = match[0]
        else:
            print("Saved device '%s' not found; running setup again." % cfg.get("device", ""))
            j = choose_device(devs)
            cfg = setup(j, vj, devs)
        if "vjoy" not in cfg:
            print("Measuring vJoy axis mapping (first run of this version)...")
            cfg["vjoy"] = calibrate_vjoy(vj, devs)
            save_cfg(cfg)

    run(j, vj, cfg)


if __name__ == "__main__":
    main()
