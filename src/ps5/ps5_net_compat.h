/*
 * PS5 Yamagi Quake II - Native Quake II port for PlayStation 5.
 * Copyright (C) 2026 BlackBearReloaded
 * SPDX-License-Identifier: GPL-3.0-or-later
 */

#ifndef PS5_NET_COMPAT_H
#define PS5_NET_COMPAT_H

#include <errno.h>
#include <netdb.h>

/* Some native libc versions leave these optional imports unresolved. Fail
 * address resolution normally; the engine's local loopback needs no resolver. */
extern __typeof__(getaddrinfo) getaddrinfo __attribute__((weak));
extern __typeof__(freeaddrinfo) freeaddrinfo __attribute__((weak));
extern __typeof__(gai_strerror) gai_strerror __attribute__((weak));

static inline int
ps5_getaddrinfo(const char *node, const char *service,
    const struct addrinfo *hints, struct addrinfo **result)
{
    *result = NULL;
    if (!getaddrinfo || !freeaddrinfo || !gai_strerror) {
        errno = ENOSYS;
        return EAI_SYSTEM;
    }
    return getaddrinfo(node, service, hints, result);
}

static inline const char *ps5_gai_strerror(int error)
{
    return gai_strerror ? gai_strerror(error) : "Native address resolver unavailable";
}

#define getaddrinfo ps5_getaddrinfo
#define gai_strerror ps5_gai_strerror
#endif
