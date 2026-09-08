#!/usr/bin/env python3
"""Compile the actual lifecycle with a fake clock; no engine, GPU or console."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

root = Path(__file__).resolve().parents[1]
harness = r'''
#define _POSIX_C_SOURCE 200809L
#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include <time.h>
#include <unistd.h>
static int64_t fake_us = 1000000;
static unsigned clock_calls, fail_call;
static const char *result_path;
static int fake_clock_gettime(clockid_t clock, struct timespec *value)
{
    assert(clock == CLOCK_MONOTONIC);
    if (++clock_calls == fail_call) return -1;
    value->tv_sec = fake_us / 1000000;
    value->tv_nsec = fake_us % 1000000 * 1000;
    return 0;
}
#define clock_gettime fake_clock_gettime
#define YQ2_PS5_RESULT_PATH result_path
#include "src/ps5/ps5_lifecycle.c"
int main(int argc, char **argv)
{
    assert(argc == 3);
    const char *scenario = argv[1];
    result_path = argv[2];
    if (!strcmp(scenario, "clock-start")) fail_call = 1;
    ps5_frame_start();
    assert(strcmp(scenario, "clock-start")); /* Startup must reject bad clock. */
    if (!strcmp(scenario, "normal")) {
        ps5_record_present();
        ps5_record_present();
        fake_us += 70000000;
        assert(ps5_frame_should_quit() == (YQ2_PS5_RUN_SECONDS > 0));
        assert(ps5_frame_stop(0) == 0);
    } else if (!strcmp(scenario, "cleanup")) {
        ps5_record_failure();
        assert(ps5_frame_stop(0) == 1);
    } else if (!strcmp(scenario, "clock-loop")) {
        fail_call = clock_calls + 1;
        assert(ps5_frame_should_quit() == 1);
        assert(ps5_frame_stop(0) == 1);
    } else if (!strcmp(scenario, "clock-event")) {
        fail_call = clock_calls + 1;
        ps5_record_present(); /* Later clock recovery must not erase this failure. */
        assert(ps5_frame_stop(0) == 1);
    } else if (!strcmp(scenario, "close-error")) {
        assert(close(fileno(result_file)) == 0);
        assert(ps5_frame_stop(0) == 1);
    } else {
        assert(!"unknown scenario");
    }
    return 0;
}
'''


def main():
    compiler = os.environ.get("CC") or shutil.which("clang-18") or shutil.which("cc")
    if not compiler:
        raise SystemExit("A host C compiler is required")
    with tempfile.TemporaryDirectory(prefix="yamagi-lifecycle-") as folder:
        temporary = Path(folder)
        source = temporary / "lifecycle.c"
        source.write_text(harness)
        for bound in (0, 60):
            executable = temporary / f"lifecycle-{bound}"
            flags = [] if bound == 0 else [f"-DYQ2_PS5_RUN_SECONDS={bound}"]
            subprocess.run([compiler, "-std=c11", "-Wall", "-Wextra", "-Werror",
                            *flags, "-I", str(root), str(source), "-o", str(executable)], check=True)
            for scenario in ("normal", "cleanup", "clock-start", "clock-loop", "clock-event", "close-error"):
                receipt = temporary / f"{bound}-{scenario}.jsonl"
                result = subprocess.run([executable, scenario, receipt], capture_output=True, text=True)
                assert result.returncode == (1 if scenario == "clock-start" else 0), result.stderr
                if scenario == "clock-start":
                    assert "CLOCK_MONOTONIC is unavailable" in result.stderr
                    continue
                events = [json.loads(line) for line in receipt.read_text().splitlines()]
                assert all(event["elapsed_us"] >= 0 for event in events)
                if scenario == "normal":
                    assert [event["event"] for event in events if event["event"] != "frame-progress"] == (
                        ["start", "first-frame"] + (["deadline"] if bound else []) + ["complete"])
                    assert events[1]["frames"] == 1 and events[-1]["frames"] == 2
                    assert events[-1]["elapsed_us"] == 70000000
                elif scenario != "close-error":
                    assert events[-1]["event"] == "failed"
                assert f"shutdown status={int(scenario != 'normal')}" in result.stdout
    print("PASS: actual lifecycle, unlimited >60s, bounded stop, first frame, clock and cleanup failures")


if __name__ == "__main__":
    main()
