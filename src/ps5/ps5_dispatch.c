/*
 * PS5 Yamagi Quake II - Native Quake II port for PlayStation 5.
 * Copyright (C) 2026 BlackBearReloaded
 * SPDX-License-Identifier: GPL-3.0-or-later
 */

#include "../../upstream/yquake2/src/client/vid/header/ref.h"

extern refexport_t GetRefAPI(refimport_t import);

refexport_t
PS5_GetRefAPI(refimport_t import)
{
	return GetRefAPI(import);
}
