"""
Contains fine-grained locking operations for shared memory
numpy arrays. We maintain the same Numpy API and perform the
locking transparently against that.
"""

import numpy as np
from os import getpid
import thread
from threading import currentThread
from numpush.shmem_sync import SharedExclusiveLock

try:
    from greenlet import getcurrent
    have_greenlet = True
except:
    have_greenlet = False

PyObject_BinaryOperators = [
    ('or','|'),  ('and','&'), ('xor','^'), ('lshift','<<'), ('rshift','>>'),
    ('add','+'), ('sub','-'), ('mul','*'), ('div','/'), ('mod','%'),
    ('truediv','/'), ('floordiv','//'), ('lt','<'), ('gt','>'), ('le','<='),
    ('ge','>='), ('eq','=='), ('ne','!=')
]

PyObject_UnaryOperators = [
    ('neg','-'), ('pos','+'), ('invert','~')
]

PyObject_Intrinsics = [
    'repr', 'str', 'hash', 'len', 'abs', 'complex', 'int', 'long', 'float',
    'iter', 'oct', 'hex'
]

PyArray_Intrinsics = [
    "dtype", "size"
]

PyArray_WriteMethods = [
    'fill', 'itemset', 'put'
]

PyArray_ReadMethods = [
    'all', 'any', 'argmax', 'argmin', 'argsort', 'astype', 'base',
    'byteswap', 'choose', 'clip', 'compress', 'conj', 'conjugate',
    'copy', 'ctypes', 'cumprod', 'cumsum', 'data', 'diagonal', 'dot',
    'dtype', 'dump', 'dumps', 'flags', 'flat', 'flatten', 'getfield',
    'imag', 'item', 'itemset', 'itemsize', 'max', 'mean',
    'min', 'nbytes', 'ndim', 'newbyteorder', 'nonzero', 'prod', 'ptp',
    'ravel', 'real', 'repeat', 'reshape', 'resize', 'round',
    'searchsorted', 'setasflat', 'setfield', 'setflags', 'shape',
    'size', 'sort', 'squeeze', 'std', 'strides', 'sum', 'swapaxes',
    'take', 'tofile', 'tolist', 'tostring', 'trace', 'transpose', 'var',
    'view'
]

class sview(np.ndarray):

    def __new__(cls, arr):
        if isinstance(arr, cls):
            raise Exception("y u do this?")
        obj = np.asarray(arr).view(type=cls)
        obj.of = id(arr)
        return obj

    def __array_finalize__(self, obj):
        if obj is None:
            return

        # The only difference between between this and vanilla views is
        # that we track the concurrency "substrate" of origin whatever
        # that may be greenlet, pthread, process, etc.
        self.thread = currentThread()
        #self.thread = thread.get_ident
        self.pid    = getpid()
        if have_greenlet:
            self.greenlet = getcurrent()

class SyncNumpy(object):

    def __init__(self, arr):
        self._underlying = arr

        self._lock = SharedExclusiveLock()

        self.reading = self._lock
        self.writing = self._lock.writing

    def data(self):
        raise Exception("Can't access underlying data for SyncNumpy.")

    def __unsafe_peek__(self):
        """
        Peek at the underlying array, for debugging.
        """
        return self._underlying

    def __array__(self):
        with self.reading:
            return self._underlying

    def __getitem__(self, i):
        with self.reading:
            return self._underlying[i]

    def __setitem__(self, i, value):
        with self.writing():
            self._underlying[i] = value

    def __getslice__(self, start, stop):
        with self.reading:
            return self._underlying[start:stop]

    def __setslice__(self, start, stop, values):
        with self.writing():
            self._underlying[start:stop] = values

    def __contains__(self,ob):
        with self.reading:
            return ob in self._underlying

    def __nonzero__(self):
        with self.reading:
            return bool(self._underlying)

    def __pow__(self,*args):
        with self.reading:
            return pow(self._underlying,*args)

    def __ipow__(self,ob):
        with self.writing():
            self._underlying **= ob
            return self

    def __rpow__(self,ob):
        with self.reading:
            return pow(ob,self._underlying)

    @property
    def size(self):
        return self._underlying.size

    @property
    def dtype(self):
        return self._underlying.dtype

    # Read Operations
    # ===============

    # Python Intrinsics
    # -----------------
    for name in PyObject_Intrinsics:
        exec (
            "def __%(name)s__(self,*args, **kwargs):\n"
            "    with self.reading:"
            "        return self._underlying.__%(name)s__()"
        ) % locals()

    # Unary Prefix
    # ------------
    for name, op in PyObject_UnaryOperators:
        exec (
            "def __%(name)s__(self):\n"
            "    with self.reading:\n"
            "        return self._underlying.__%(name)s__()"
        ) % locals()

    for name in PyArray_ReadMethods:
        exec (
            "def %(name)s(self, *args, **kwargs):\n"
            "    with self.reading:\n"
            "        return self._underlying.%(name)s(*args, **kwargs)"
        ) % locals()

    # Binary Prefix
    # -------------
    for name, op in PyObject_BinaryOperators:
        exec (
            "def __%(name)s__(self,ob):\n"
            "    with self.reading:"
            "        return self._underlying %(op)s ob\n"
            "\n"
            "def __r%(name)s__(self,ob):\n"
            "    with self.reading:"
            "        return ob %(op)s self._underlying\n"
            "\n"
        )  % locals()

    # Write Operations
    # ===============

    for name, op in PyObject_BinaryOperators:
        exec (
            "def __i%(name)s__(self,ob):\n"
            "    with self.writing:"
            "        return ob %(op)s self._underlying\n"
            "\n"
        )  % locals()

    for name in PyArray_WriteMethods:
        exec (
            "def %(name)s(self, *args, **kwargs):\n"
            "    with self.writing:\n"
            "        return self._underlying.%(name)s(*args, **kwargs)"
        ) % locals()
