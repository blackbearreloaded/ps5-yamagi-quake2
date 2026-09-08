#!/usr/bin/env python3
# PS5 Yamagi Quake II - Native Quake II port for PlayStation 5.
# Copyright (C) 2026 BlackBearReloaded
# SPDX-License-Identifier: GPL-3.0-or-later

"""Check playable controller defaults and preserve upstream user overrides."""
from pathlib import Path
import re
import shlex

root = Path(__file__).resolve().parents[1]
expected = {"TRIG_RIGHT": "+attack", "BTN_SOUTH": "+moveup", "BTN_EAST": "+movedown",
            "SHOULDR_LEFT": "weapprev", "SHOULDR_RIGHT": "weapnext", "STICK_LEFT": "+speed",
            "BTN_NORTH": "inven", "BTN_WEST": "invuse", "DP_UP": "invprev",
            "DP_DOWN": "invnext", "TOUCHPAD": "cmd help"}
bindings = {}
for line in (root / "assets/baseq2/yq2.cfg").read_text().splitlines():
    if not line.strip() or line.lstrip().startswith("//"):
        continue
    command, key, action = shlex.split(line)
    if command == "set":
        assert (key, action) in (("s_khz", "48"), ("cl_showfps", "1"))
        continue
    assert command == "bind" and key not in bindings, line
    bindings[key] = action
assert bindings == expected, bindings

keyboard = (root / "upstream/yquake2/src/client/cl_keyboard.c").read_text()
keys = keyboard.split("static char *gamepadbtns[] =", 1)[1].split("};", 1)[0]
assert set(bindings) <= set(re.findall(r'"([^"\n]+)"', keys))
frame = (root / "upstream/yquake2/src/common/frame.c").read_text()
config_order = frame.split("void Qcommon_ExecConfigs(", 1)[1].split("static qboolean", 1)[0]
assert re.findall(r'exec ([a-z0-9.]+)\\n', config_order) == [
    "default.cfg", "yq2.cfg", "config.cfg", "autoexec.cfg"]
build = (root / "tools/build-ps5.sh").read_text()
assert 'cp -a "$root/assets/." "$stage/assets/"' in build
print("PASS: gamepad actions use supported keys; defaults load before user config and are packaged")
