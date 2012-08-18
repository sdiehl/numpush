import os
import sys
import socket
import platform
import resource
from numpy.distutils.cpuinfo import cpuinfo
from zmq import zmq_version

CPU       = cpuinfo
PLATFORM  = platform.system()
ARCH      = platform.architecture()
MAX_PROCS = resource.getrlimit(resource.RLIMIT_NPROC)[1]
MAX_FDS   = resource.getrlimit(resource.RLIMIT_NOFILE)[1]
PAGESIZE  = resource.getpagesize()
HOSTNAME  = socket.gethostname()
PYPY      = hasattr(sys, 'pypy_version_info')
CPYTHON   = not PYPY
ZMQ       = zmq_version()
SSE2      = 'sse2' in open('/proc/cpuinfo','r').read()

try:
    socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDPLITE);
    UDPLITE = True
except:
    UDPLITE = False

try:
    socket.socket(socket.AF_TIPC, socket.SOCK_RDM)
    TIPC = True
except:
    TIPC = False

try:
    os.stat('/usr/include/pthread.h')
    PTHREADS = True
except:
    PTHREADS = False
    pass
