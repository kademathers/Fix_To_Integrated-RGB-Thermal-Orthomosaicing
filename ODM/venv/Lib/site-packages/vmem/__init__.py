name = "vmem"

import os, sys

if os.name == 'nt':
    from .windows import virtual_memory
else:
    if sys.platform == 'darwin':
        from .osx import virtual_memory
    else:
        from .posix import virtual_memory