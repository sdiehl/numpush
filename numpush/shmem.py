from numpy import ndarray, byte_bounds
from pandas import DataFrame
from functools import wraps

from multiprocessing.heap import BufferWrapper

def lock(arr):
    arr.flags.writable = False
    return byte_bounds(arr)

def unlock(arr):
    arr.flags.writable = True
    return byte_bounds(arr)

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
    mmap_nd[:] = array[:]
    assert mmap_nd.ctypes.data == address
    # TODO: agnostic backend
    return SynchronizedArray(mmap_nd, lock=lock)

def sync(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        self = args[0]
        self.acquire()
        f(*args, **kwargs)
        self.release()
    return wrapper


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

def STensor(tensor, mutex=False):
    '''
    Shared memory Theano tensor.
    '''
    pass

def SDiGraph(graph, mutex=False):
    '''
    Shared memory NetworkX graph.
    '''
    pass
