<!--
PS5 Yamagi Quake II - Native Quake II port for PlayStation 5.
Copyright (C) 2026 BlackBearReloaded
SPDX-License-Identifier: GPL-3.0-or-later
-->

# Selection audio

The project owner supplied quake2.mp3 for the shell selection music. The full
approximately 44-second track is included as snd0.at9; the source MP3 is local.

Converted using the manual workflow in the [ps5-at9-converter manual workflow](https://github.com/blackbearreloaded/ps5-at9-converter#manual-conversion-recommended):
- FFmpeg: remove metadata, loudnorm=I=-28:LRA=11:TP=-2, 48 kHz stereo PCM16.
- User-supplied ps4_at9tool.exe: -e -br 192 -wholeloop.
- Result: 1,055,400 bytes, below the 2,097,152-byte shell limit.
- Package presentation validator passed format, size and loop-metadata checks.
- Independent FFmpeg decode passed; measured -27.2 LUFS and -12.4 dBFS true peak.

Source SHA-256: ac766c7436c4419f234fdbc6a8ce0e21d7d7c1131cf76970f5a3bfdf32d1f4a6
snd0.at9 SHA-256: af133744046c4de95b592e110a043c5146f17228155e832c05e9b8c7700199a2

The builder copies sce_sys/snd0.at9 into the app presentation directory. The existing
pubtools.loudnessSnd0 value in param.json is -28.00. The release package
also includes the song. No console deployment or shell playback test was performed.
After deployment, the documented workflow requires a full ShadowMountPlus restart
or console restart before checking changed presentation assets.

Conversion and decode evidence: build/shell-audio/ (ignored).
