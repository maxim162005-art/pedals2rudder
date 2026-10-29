# -*- coding: utf-8 -*-
"""Unit checks for the pure maths in rudder.py.  Run:  python tests/test_mix.py
No hardware needed (pygame must be installed because rudder.py imports it)."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import rudder  # noqa: E402

cases = [
    # (left, right)   expected rudder, expected brake (None = see note check)
    ((0.0, 0.0),  0.0,  0.0,  "both released -> neutral, no brake"),
    ((1.0, 0.0), -1.0,  0.0,  "left only, full -> full left rudder"),
    ((0.0, 1.0), +1.0,  0.0,  "right only, full -> full right rudder"),
    ((0.5, 0.0), -0.5,  0.0,  "left half -> half left rudder"),
    ((1.0, 1.0),  0.0,  1.0,  "both full -> full brake, rudder straight"),
    ((0.8, 0.6),  0.0,  None, "both, 20% diff < 30% tol -> brake, rudder straight"),
    ((0.6, 0.8),  0.0,  None, "same, other way round"),
    ((0.5, 0.5),  0.0,  None, "both half -> brake ~41%, rudder straight"),
    ((1.0, 0.3),  None, None, "left full, right 30% -> light brake, rudder LEFT"),
    ((0.1, 0.1),  0.0,  0.0,  "both 10% < 15% threshold -> nothing"),
    ((0.1, 0.5), +0.4,  0.0,  "right 50%, left 10% (< threshold) -> rudder, not brake"),
]
fails = 0
for (l, r), er, eb, note in cases:
    rud, brk = rudder.mix(l, r)
    ok = True
    if er is not None and abs(rud - er) > 1e-9:
        ok = False
    if eb is not None and abs(brk - eb) > 1e-9:
        ok = False
    if note.endswith("rudder LEFT") and not (rud < 0 and 0 < brk < 0.3):
        ok = False
    if "brake ~41%" in note and not (0.40 < brk < 0.42):
        ok = False
    if eb is None and er == 0.0 and "brake" in note and brk <= 0:
        ok = False
    print("%s  L=%.1f R=%.1f -> rudder %+.3f brake %.3f   %s"
          % ("OK  " if ok else "FAIL", l, r, rud, brk, note))
    fails += (not ok)

nominal = rudder.VJOY_DEFAULT
got = [rudder.to_raw(v, nominal) for v in (-1, 0, 1)]
print("to_raw nominal (-1,0,+1) ->", got, "OK" if got == [0, 16384, 32768] else "FAIL")
fails += got != [0, 16384, 32768]

skewed = {"lo": 4600, "center": 17100, "hi": 31100}
got = [rudder.to_raw(v, skewed) for v in (-1, -0.5, 0, 0.5, 1)]
exp = [4600, 10850, 17100, 24100, 31100]
print("to_raw skewed            ->", got, "OK" if got == exp else "FAIL")
fails += got != exp

c = {"rest": -1.0, "pressed": 1.0}
got = [round(rudder.norm(v, c, 0.04), 3) for v in (-1.0, -0.95, 0.0, 1.0)]
print("norm (-1,-0.95,0,+1)     ->", got, "OK" if got[0] == 0 and got[3] == 1 and 0 < got[2] < 0.6 else "FAIL")
fails += not (got[0] == 0 and got[3] == 1 and 0 < got[2] < 0.6)

print("\nRESULT:", "all checks passed" if fails == 0 else "%d failures" % fails)
sys.exit(1 if fails else 0)
