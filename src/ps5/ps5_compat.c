/*
 * PS5 Yamagi Quake II - Native Quake II port for PlayStation 5.
 * Copyright (C) 2026 BlackBearReloaded
 * SPDX-License-Identifier: GPL-3.0-or-later
 */

#include <stddef.h>

int if_nametoindex(const char *name)
{
	(void)name;
	return 0;
}

const char *nl_langinfo(int item)
{
	(void)item;
	return "UTF-8";
}

int ___mb_cur_max(void)
{
	return 1;
}
