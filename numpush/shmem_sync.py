import numpy as np
from threading import currentThread
from contextlib import contextmanager

from _multiprocessing import SemLock
from multiprocessing import BoundedSemaphore, Semaphore, Condition, Event
from multiprocessing.util import register_after_fork
from multiprocessing.forking import assert_spawning, Popen

# The counter is decremented when the semaphore is acquired, and
# incremented when the semaphore is released. If the counter reaches zero
# when acquired, the acquiring thread will block.

class SharedExclusiveLock(object):

    def __init__(self, maxreaders=120):
        # Linux max semaphore sets is 120
        self.max = 120
        self._reader   = Semaphore(120)
        self._writer   = Semaphore(1)
        self._sleeping = Event()

        # Does this process hold the write?
        self.localwrite = False
        self.thread_id = currentThread()

        self.create_methods()

        def after_fork(obj):
            obj._reader._after_fork()
            obj._writer._after_fork()
            obj._sleeping._after_fork()

        register_after_fork(self, after_fork)

    def create_methods(self):
        self.acquire = self._reader.acquire
        self.release = self._reader.release

    @property
    def ismine(self):
        return self.localwrite and (currentThread() == self.thread_id)

    # you can nest write calls
    def wait_noreaders(self):
        if self.ismine:
            return
        while self._reader.get_value() < self.max:
            self._sleeping.set()
            # twiddle the futex
            self._sleeping.wait()

    @contextmanager
    def writing(self):
        if self.ismine:
            yield
        else:
            self.wait_noreaders()
            self._writer.acquire()
            self.localwrite = True
            yield
            self.localwrite = False
            self._writer.release()

    def __enter__(self, blocking=True, timeout=None):
        # prevent writer starvation
        if self.ismine:
            return
        else:
            self._reader.acquire()

    def __exit__(self, *args):
        if self.ismine:
            return
        else:
            self._reader.release()
            if self._sleeping.is_set():
                # twiddle the futex
                self._sleeping.clear()

    def __getstate__(self):
        assert_spawning(self)
        r = self._reader._semlock
        w = self._writer._semlock

        reader = Popen.duplicate_for_child(r.handle), r.kind, r.maxvalue
        writer = Popen.duplicate_for_child(w.handle), w.kind, w.maxvalue
        return (reader, writer)

    def __setstate__(self, state):
        reader, writer = state
        self._reader = SemLock._rebuild(*reader)
        self._writer = SemLock._rebuild(*writer)
