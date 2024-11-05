# Copyright (c) 2009, Giampaolo Rodola'. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.
import resource

from .utils import svmem, usage_percent

def calculate_avail_vmem(mems):
    """Fallback for kernels < 3.14 where /proc/meminfo does not provide
    "MemAvailable:" column, see:
    https://blog.famzah.net/2014/09/24/
    This code reimplements the algorithm outlined here:
    https://git.kernel.org/cgit/linux/kernel/git/torvalds/linux.git/
        commit/?id=34e431b0ae398fc54ea69ff85ec700722c9da773
    XXX: on recent kernels this calculation differs by ~1.5% than
    "MemAvailable:" as it's calculated slightly differently, see:
    https://gitlab.com/procps-ng/procps/issues/42
    https://github.com/famzah/linux-memavailable-procfs/issues/2
    It is still way more realistic than doing (free + cached) though.
    """
    # Fallback for very old distros. According to
    # https://git.kernel.org/cgit/linux/kernel/git/torvalds/linux.git/
    #     commit/?id=34e431b0ae398fc54ea69ff85ec700722c9da773
    # ...long ago "avail" was calculated as (free + cached).
    # We might fallback in such cases:
    # "Active(file)" not available: 2.6.28 / Dec 2008
    # "Inactive(file)" not available: 2.6.28 / Dec 2008
    # "SReclaimable:" not available: 2.6.19 / Nov 2006
    # /proc/zoneinfo not available: 2.6.13 / Aug 2005
    free = mems[b'MemFree:']
    fallback = free + mems.get(b"Cached:", 0)
    try:
        lru_active_file = mems[b'Active(file):']
        lru_inactive_file = mems[b'Inactive(file):']
        slab_reclaimable = mems[b'SReclaimable:']
    except KeyError:
        return fallback
    try:
        f = open('/proc/zoneinfo', 'rb')
    except IOError:
        return fallback  # kernel 2.6.13

    watermark_low = 0
    with f:
        for line in f:
            line = line.strip()
            if line.startswith(b'low'):
                watermark_low += int(line.split()[1])
    watermark_low *= resource.getpagesize()

    avail = free - watermark_low
    pagecache = lru_active_file + lru_inactive_file
    pagecache -= min(pagecache / 2, watermark_low)
    avail += pagecache
    avail += slab_reclaimable - min(slab_reclaimable / 2.0, watermark_low)
    return int(avail)

def virtual_memory():
    """Report virtual memory stats.
    This implementation matches "free" and "vmstat -s" cmdline
    utility values and procps-ng-3.3.12 source was used as a reference
    (2016-09-18):
    https://gitlab.com/procps-ng/procps/blob/
        24fd2605c51fccc375ab0287cec33aa767f06718/proc/sysinfo.c
    For reference, procps-ng-3.3.10 is the version available on Ubuntu
    16.04.
    Note about "available" memory: up until psutil 4.3 it was
    calculated as "avail = (free + buffers + cached)". Now
    "MemAvailable:" column (kernel 3.14) from /proc/meminfo is used as
    it's more accurate.
    That matches "available" column in newer versions of "free".
    """
    mems = {}
    with open('/proc/meminfo', 'rb') as f:
        for line in f:
            fields = line.split()
            mems[fields[0]] = int(fields[1]) * 1024

    # /proc doc states that the available fields in /proc/meminfo vary
    # by architecture and compile options, but these 3 values are also
    # returned by sysinfo(2); as such we assume they are always there.
    total = mems[b'MemTotal:']
    free = mems[b'MemFree:']
    try:
        buffers = mems[b'Buffers:']
    except KeyError:
        buffers = 0

    try:
        cached = mems[b"Cached:"]
    except KeyError:
        cached = 0
    else:
        # "free" cmdline utility sums reclaimable to cached.
        # Older versions of procps used to add slab memory instead.
        # This got changed in:
        # https://gitlab.com/procps-ng/procps/commit/
        #     05d751c4f076a2f0118b914c5e51cfbb4762ad8e
        cached += mems.get(b"SReclaimable:", 0)  # since kernel 2.6.19

    used = total - free - cached - buffers
    if used < 0:
        # May be symptomatic of running within a LCX container where such
        # values will be dramatically distorted over those of the host.
        used = total - free

    # - starting from 4.4.0 we match free's "available" column.
    #   Before 4.4.0 we calculated it as (free + buffers + cached)
    #   which matched htop.
    # - free and htop available memory differs as per:
    #   http://askubuntu.com/a/369589
    #   http://unix.stackexchange.com/a/65852/168884
    # - MemAvailable has been introduced in kernel 3.14
    try:
        avail = mems[b'MemAvailable:']
    except KeyError:
        avail = calculate_avail_vmem(mems)

    if avail < 0:
        avail = 0

    # If avail is greater than total or our calculation overflows,
    # that's symptomatic of running within a LCX container where such
    # values will be dramatically distorted over those of the host.
    # https://gitlab.com/procps-ng/procps/blob/
    #     24fd2605c51fccc375ab0287cec33aa767f06718/proc/sysinfo.c#L764
    if avail > total:
        avail = free

    percent = usage_percent((total - avail), total, round_=1)

    return svmem(total, avail, percent, used, free)
