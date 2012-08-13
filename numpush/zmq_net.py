import zmq
import ctypes
import reductor

import numpy as np
from numpy import ndarray, array

from pandas import DataFrame
#from theano.tensor import Tensor
from collections import namedtuple
from datastructures import ReverseLookupDict

try:
    import msgpack as srl
except ImportError:
    import cPickle as srl

numpy_metadata  = namedtuple('metadata', 'shape dtype')
tensor_metadata = namedtuple('metadata', 'shape dtype')
pandas_metadata = namedtuple('metadata', 'shape dtype index columns')

# Pad the wire protocol so that we can recognize types on the receiving
# side. The most common numpy data transfers are likely 1 or 2
# dimensional arrays, so we have special bit flag for those to avoid
# serializing metadata.

ctypes_numpy = ReverseLookupDict({
    ctypes.c_char   : np.int8,
    ctypes.c_wchar  : np.int16,
    ctypes.c_byte   : np.int8,
    ctypes.c_ubyte  : np.uint8,
    ctypes.c_short  : np.int16,
    ctypes.c_ushort : np.uint16,
    ctypes.c_int    : np.int32,
    ctypes.c_uint   : np.int32,
    ctypes.c_long   : np.int32,
    ctypes.c_ulong  : np.int32,
    ctypes.c_float  : np.float32,
    ctypes.c_double : np.float64
})

NUMPYND  = b'\x00\x01'
NUMPY1D  = b'\x00\x02'
NUMPY2D  = b'\x00\x03'
PANDAS   = b'\x00\x04'
PANDASTS = b'\x00\x05'
NETWORKX = b'\x00\x06'
THEANO   = b'\x00\x07'

type_coercions = {
    array     : NUMPYND,
    ndarray   : NUMPYND,
    DataFrame : PANDAS,
    #Tensor    : THEANO,
}

class CannotCoerce(Exception):
    def __init__(self, obj):
        self.unknown_type = type(obj)

    def __str__(self):
        return "Don't know how encode type %s over ZMQ" % ( self.unknown_type)

def send_numpy(self, magic, obj, flags=0):
    numpy_metadata, narray = reductor.numpy_reduce(obj)
    self.send(magic, flags|zmq.SNDMORE)
    self.send(srl.dumps(numpy_metadata), flags|zmq.SNDMORE)
    return self.send(narray, flags, copy=False, track=False)

def recv_numpy(self, flags=0, copy=True, track=False):
    mdload = srl.loads(self.recv(flags=flags))
    md = numpy_metadata(*mdload)
    nd = self.recv(flags=flags)
    return reductor.numpy_reconstruct(md, nd)

def send_pandas(self, magic, obj, flags=0):
    pandas_metadata, narray = reductor.pandas_reduce(obj)
    self.send(magic, flags|zmq.SNDMORE)
    self.send(srl.dumps(pandas_metadata), flags|zmq.SNDMORE)
    return self.send(narray, flags, copy=False, track=False)

def recv_pandas(self, flags=0, copy=True, track=False):
    mdload = srl.loads(self.recv(flags=flags))
    md = pandas_metadata(*mdload)
    nd = self.recv(flags=flags)
    return reductor.pandasts_reconstruct(md, nd)

def send_tensor(self, magic, obj, flags=0):
    tensor_metadata, narray = reductor.tensor_reduce(obj)
    self.send(magic, flags|zmq.SNDMORE)
    self.send(srl.dumps(tensor_metadata), flags|zmq.SNDMORE)
    return self.send(narray, flags, copy=False, track=False)

def recv_tensor(self, flags=0, copy=True, track=False):
    mdload = srl.loads(self.recv(flags=flags))
    md = tensor_metadata(*mdload)
    nd = self.recv(flags=flags)
    return reductor.tensor_reconstruct(md, nd)

# Polymorphic ZMQ socket mixins for all supported scientific types
def numsend(self, obj, **kwargs):
    magic = type_coercions.get(type(obj))
    if magic ==  NUMPYND:
        send_numpy(self, magic, obj, **kwargs)
    elif magic == PANDAS:
        send_pandas(self, magic, obj, **kwargs)
    else:
        raise CannotCoerce(obj)

def numrecv(self, **kwargs):
    magic = self.recv()
    if magic in [NUMPYND, NUMPY1D, NUMPY2D]:
        return recv_numpy(self, **kwargs)
    elif magic == PANDAS:
        return recv_pandas(self, **kwargs)
    else:
        raise Exception("Unknown wire protocol")
