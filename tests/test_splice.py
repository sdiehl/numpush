import _multiprocessing
#from unittest2 import skip

import sys
import os
import socket
sys.path.append(os.getcwd())
from numpush.posix_io.splice import \
    posix_splice, \
    posix_splice_thread, \
    posix_splice_sockets, \
    SPLICE_MORE, SPLICE_MOVE

DATA= 'a'*1024

def test_single():
    os.mkfifo('w')
    os.mkfifo('r')

    try:
        w = open('w', 'w+')
        r = open('r', 'a+')

        w.write(DATA)
        w.flush()

        flags = SPLICE_MORE | SPLICE_MOVE
        posix_splice(w, r, 1024, flags)

        assert r.read(1024) == DATA

    finally:
        os.unlink('w')
        os.unlink('r')

def test_multithreaded():
    os.mkfifo('w')
    os.mkfifo('r')

    try:
        w = open('w', 'w+')
        r = open('r', 'a+')

        w.write(DATA)
        w.flush()

        flags = SPLICE_MORE | SPLICE_MOVE
        thread = posix_splice_thread(w, r, 1024, flags)
        thread.join()
        assert r.read(1024) == DATA

    finally:
        os.unlink('w')
        os.unlink('r')
