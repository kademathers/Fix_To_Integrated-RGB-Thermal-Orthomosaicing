# Copyright (c) 2009, Giampaolo Rodola'. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.
from collections import namedtuple

svmem = namedtuple(
    'svmem', ['total', 'available', 'percent', 'used', 'free'])

def usage_percent(used, total, round_=None):
    """Calculate percentage usage of 'used' against 'total'."""
    try:
        ret = (float(used) / total) * 100
    except ZeroDivisionError:
        return 0.0
    else:
        if round_ is not None:
            ret = round(ret, round_)
        return ret
