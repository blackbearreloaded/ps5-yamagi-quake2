#define _POSIX_C_SOURCE 200809L

#include "ps5_lifecycle.h"

#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <time.h>

#ifdef YQ2_PS5
#define exit ps5_exit
#endif

#ifndef YQ2_PS5_RUN_SECONDS
#define YQ2_PS5_RUN_SECONDS 0
#endif

#ifndef YQ2_PS5_RESULT_PATH
#define YQ2_PS5_RESULT_PATH "/download0/yamagi-result.jsonl"
#endif

static FILE *result_file;
static int64_t deadline_us;
static int64_t start_us;
static uint64_t presented_frames;
static int stopped;
static int failed;

static int64_t
ps5_monotonic_us(void)
{
	struct timespec now;

	if (clock_gettime(CLOCK_MONOTONIC, &now) != 0)
		return -1;
	return (int64_t)now.tv_sec * 1000000 + now.tv_nsec / 1000;
}

static void
ps5_write_event(const char *event)
{
	if (result_file == NULL)
		return;
	int64_t now = ps5_monotonic_us();
	if (now < start_us) { failed = 1; return; }
	if (fprintf(result_file, "{\"event\":\"%s\",\"frames\":%llu,\"elapsed_us\":%lld}\n",
		event, (unsigned long long)presented_frames,
		(long long)(now - start_us)) < 0 || fflush(result_file) != 0)
		failed = 1;
}

void
ps5_frame_start(void)
{
	start_us = ps5_monotonic_us();
	if (start_us < 0)
	{
		fputs("[ps5] CLOCK_MONOTONIC is unavailable\n", stderr);
		exit(EXIT_FAILURE);
	}
	deadline_us = YQ2_PS5_RUN_SECONDS > 0 ?
		start_us + (int64_t)YQ2_PS5_RUN_SECONDS * 1000000 : 0;
	result_file = fopen(YQ2_PS5_RESULT_PATH, "wb");
	if (result_file == NULL)
	{
		fprintf(stderr, "[ps5] cannot open result path: %s\n", YQ2_PS5_RESULT_PATH);
		exit(EXIT_FAILURE);
	}
	ps5_write_event("start");
}

int
ps5_frame_should_quit(void)
{
	int64_t now = ps5_monotonic_us();
	if (now < start_us)
	{
		failed = 1;
		stopped = 1;
	}
	if (!stopped && deadline_us && now >= deadline_us)
	{
		stopped = 1;
		ps5_write_event("deadline");
	}
	return stopped;
}

void ps5_record_failure(void) { failed = 1; }

int ps5_frame_stop(int status)
{
	status = status || failed;
	ps5_write_event(status ? "failed" : "complete");
	status = status || failed;
	if (result_file && fclose(result_file) != 0) status = 1;
	result_file = NULL;
	printf("[yamagi-ps5] shutdown status=%d frames=%llu\n", status,
		(unsigned long long)presented_frames);
	return status;
}

void
ps5_record_present(void)
{
	++presented_frames;
	if (presented_frames == 1) ps5_write_event("first-frame");
	if (presented_frames <= 5 || presented_frames % 120 == 0)
		ps5_write_event("frame-progress");
	if (presented_frames == 1 || presented_frames % 120 == 0)
	{
		fflush(stdout);
		fflush(stderr);
	}
}
