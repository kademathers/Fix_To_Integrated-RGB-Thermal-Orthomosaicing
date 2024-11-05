import resource
import subprocess
import re

from .utils import svmem, usage_percent

sys_regex = re.compile(r'^hw\.memsize\: ([\d]+)')
vm_regex = re.compile(r'^([^:]+)\:\s+([\d]+)')

def virtual_memory():
    total = avail = percent = used = free = 0
    pagesize = resource.getpagesize()

    out = subprocess.check_output(["sysctl", "hw.memsize"])
    matches = sys_regex.match(out)
    if matches:
        total = int(matches.group(1))

        out = subprocess.check_output(["vm_stat"])
        params = {}
        for line in out.split("\n"):
            matches = vm_regex.match(line)
            if matches:
                k = matches.group(1).replace("\"", "")
                params[k] = int(matches.group(2))

        active = params.get('Pages active', 0) * pagesize
        inactive = params.get('Pages inactive', 0) * pagesize
        wired = params.get('Pages wired down', 0) * pagesize
        free = params.get('Pages free', 0) * pagesize
        speculative = params.get('Pages speculative', 0) * pagesize

        avail = inactive + free
        used = active + wired

        free -= speculative
        percent = usage_percent((total - avail), total, round_=1)

    return svmem(total, avail, percent, used, free)
