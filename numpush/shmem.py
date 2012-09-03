from numpy import ndarray
from pandas import DataFrame
from functools import wraps

from multiprocessing import RLock
from multiprocessing.heap import BufferWrapper
from multiprocessing.sharedctypes import SynchronizedBase

def put_on_heap(na):
    size = na.nbytes
    wrapper = BufferWrapper(size)
    address = wrapper.get_address()
    block, size =  wrapper._state
    arena, start, new_stop = block

    return (arena.buffer, address)

def RawNumpy(array):
    mmap, address = put_on_heap(array)
    mmap_nd = ndarray.__new__(
        ndarray,
        array.shape,
        dtype=array.dtype,
        buffer=mmap,
        offset=0,
        order='C'
    )
    # Warning, this is a copy operation
    # ---------------------------------
    # Copy the values from the passed array into shared memory
    # arena.
    mmap_nd[:] = array[:]
    assert mmap_nd.ctypes.data == address
    return mmap_nd

def SynchronizedNumpy(array, lock=None):
    mmap, address = put_on_heap(array)
    mmap_nd = ndarray.__new__(
        ndarray,
        array.shape,
        dtype  = array.dtype,
        buffer = mmap,
        offset = 0,
        order  = 'C'
    )
    # Warning, this is a copy operation
    # ---------------------------------
    # Copy the values from the passed array into shared memory
    # arena.
    mmap_nd[:] = array[:]
    assert mmap_nd.ctypes.data == address
    return SynchronizedArray(mmap_nd, lock=lock)

def sync(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        self = args[0]
        self.acquire()
        f(*args, **kwargs)
        self.release()
    return wrapper

class SynchronizedArray(SynchronizedBase):

    def __init__(self, obj, lock=None):
        self._obj = obj
        self._lock = lock or RLock()
        self.acquire = self._lock.acquire
        self.release = self._lock.release

    def __len__(self):
        return len(self._obj)

    def __getitem__(self, i):
        self.acquire()
        try:
            return self._obj[i]
        finally:
            self.release()

    def __setitem__(self, i, value):
        self.acquire()
        try:
            self._obj[i] = value
        finally:
            self.release()

    def __getslice__(self, start, stop):
        self.acquire()
        try:
            return self._obj[start:stop]
        finally:
            self.release()

    def __setslice__(self, start, stop, values):
        self.acquire()
        try:
            self._obj[start:stop] = values
        finally:
            self.release()

    def __iadd__(self, other):
        with self._lock:
            return self._obj.__iadd__(other)

    def __imul__(self, other):
        with self._lock:
            return self._obj.__imul__(other)

# Shared Memory Instances
# -----------------------

def SDataFrame(df, mutex=False, lock=None):
    '''
    Shared memory Pandas dataframe. Any number of processes can
    write on it and access it across multiple cores.
    '''
    snd = RawNumpy(df.values)
    index = df.index.tolist()    # list
    columns = df.columns.tolist()  # list
    return DataFrame(data=snd, index=index, columns=columns, dtype=None, copy=False)

def SDiGraph(graph, mutex=False):
    '''
    Shared memory NetworkX graph.
    '''
    pass

def STensor(tensor, mutex=False):
    '''
    Shared memory Theano tensor.
    '''
    pass
