import ctypes
from .utils import svmem, usage_percent

class MEMORYSTATUSEX(ctypes.Structure):
    _fields_ = [
        ("dwLength", ctypes.c_ulong),
        ("dwMemoryLoad", ctypes.c_ulong),
        ("ullTotalPhys", ctypes.c_ulonglong),
        ("ullAvailPhys", ctypes.c_ulonglong),
        ("ullTotalPageFile", ctypes.c_ulonglong),
        ("ullAvailPageFile", ctypes.c_ulonglong),
        ("ullTotalVirtual", ctypes.c_ulonglong),
        ("ullAvailVirtual", ctypes.c_ulonglong),
        ("sullAvailExtendedVirtual", ctypes.c_ulonglong),
    ]

    def __init__(self):
        # have to initialize this to the size of MEMORYSTATUSEX
        self.dwLength = ctypes.sizeof(self)
        super(MEMORYSTATUSEX, self).__init__()


def virtual_memory():
    stat = MEMORYSTATUSEX()
    ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(stat))
    total = stat.ullTotalPhys
    avail = stat.ullAvailPhys
    free = stat.ullAvailPhys
    used = total - avail
    percent = usage_percent((total - avail), total, round_=1)

    return svmem(total, avail, percent, used, free)