from io import BytesIO
from array import array
from imp import new_module
from StringIO import StringIO

try:
    from numpy import dtype, frombuffer
except ImportError:
    have_numpy = False

try:
    from pandas import DataFrame, TimeSeries
except ImportError:
    have_pandas = False

try:
    from theano.tensor import Tensor
    have_theano = True
except ImportError:
    have_theano = False

try:
    from carray import carray
    have_carray = True
except ImportError:
    have_carray = False

try:
    from nuemxpr.necompiler import NumExpr
    have_numexpr = True
except ImportError:
    have_numexpr = False

try:
    from numba.translate import Translate
    have_numba = True
except ImportError:
    have_numba = False

try:
    import cython
    have_cython = True
except ImportError:
    have_cython = False

try:
    from llvm.core import Module
    from llvm.ee import ExecutionEngine
    from bitey.bind import make_all_wrappers
    have_bitey = True
except:
    have_bitey = False


# Numpy
# =====

def numpy_reduce(nd):
    dtype_name = nd.dtype.name   # string
    shape      = nd.values.shape # tuple

    # Pandas ndarray
    nd = nd
    md = (shape, dtype_name)
    return md, nd

def numpy_reconstruct(md, nd):
    index, columns, dtype_name, shape = md
    buf = buffer(nd)

    ndarray = frombuffer(buf, dtype=dtype(dtype_name)).reshape(shape)
    return ndarray

# Pandas
# ======

# You take a Panda and you squeeze it into a zero-copy buffer, it ain't
# pretty.
def pandas_reduce(df):
    index      = df.index.tolist()    # list
    columns    = df.columns.tolist()  # list
    dtype_name = df.values.dtype.name # string
    shape      = df.values.shape      # tuple

    # Pandas ndarray
    nd = df.values
    md = (shape, dtype_name, index, columns)
    return md, nd

def pandas_reconstruct(md, nd):
    shape, ndtype, index, columns = md
    ndarray = frombuffer(nd, dtype=dtype(ndtype)).reshape(shape)
    return DataFrame(data=ndarray, index=index,
            columns=columns, dtype=None)

def pandasts_reduce(df):
    index  = df.index.tolist()    # list
    ndtype = df.values.dtype.name # string
    shape  = df.values.shape      # tuple

    # Pandas ndarray
    nd = buffer(df.values)
    md = (shape, ndtype, index)
    return md, nd

def pandasts_reconstruct(md, nd):
    index, columns, dtype_name, shape = md
    buf = buffer(nd)

    ndarray = frombuffer(buf, dtype=dtype(dtype_name)).reshape(shape)
    return TimeSeries(data=ndarray, index=index,
            columns=columns, dtype=dtype_name)

# Array
# =====

def array_reduce(pd):
    typecode   = pd.typecode

    # Pandas ndarray
    nd = buffer(pd)
    md = (typecode,)
    return md, nd

def array_reconstruct(md, nd):
    typecode, = md
    buf = buffer(nd)
    return array(typecode, buf)

# Theano
# ======

def tensor_reduce(ts):
    pass

def tensor_reconstruct(md, nd):
    pass

# NetworkX
# ========

def digraph_reduce(ts):
    pass

def digrpah_reconstruct(md, nd):
    pass

# ============
# --- Code ---
# ============

# LLVM
# =====

def bitey_reduce(module):
    if hasattr(module, '_llvm_module'):
        name = module.__name__
        bitcode = StringIO()
        module.to_bitcode(bitcode)
        return (name, bitcode)
    else:
        raise TypeError("Are you sure thats a LLVM backed Bitey module?")

def bitey_reconstruct(md, bitcode):
    name, = md

    mod = new_module(name)
    llvm_module = Module.from_bitcode(BytesIO(bitcode))
    engine = ExecutionEngine.new(llvm_module)
    make_all_wrappers(llvm_module, engine, mod)

    return mod

# Numba
# =====

LLVM  = 0
UFUNC = 1
GUFUNC = 1

# This is a little hairy since Numba is still experimental.
def numba_reduce(tr):
    func      = tr.func      # PyCodeObject
    ret_type  = tr.ret_type  # str
    arg_types = tr.arg_types # str

    return (func, ret_type, arg_types)

def numba_reduce_bitcode(tr):
    out = StringIO()
    tr.mod.to_bitcode(out)
    return (out,)

# Returns a CFunctionType or numpy.ufunc
def numba_reconstruct(md, func, otype=LLVM):
    ret_type, arg_types = md
    tr = Translate(func, ret_type, arg_types)
    tr.translate()

    if otype == LLVM:
        return tr.get_ctypes_func(llvm=True)
    elif otype == UFUNC:
        return tr.make_ufunc(llvm=True)
    elif otype == GUFUNC:
        pass
    else:
        raise Exception("Unknown numba cast")

# NumExpr
# =======

def numexpr_reduce(ne):
    # Metadata
    inputsig    = ne.signature
    tempsig     = ne.tempsig
    input_names = ne.input_names
    constants   = ne.constants

    # Bytecode
    bytecode    = ne.program

    return (inputsig, tempsig, bytecode, constants, input_names)

def numexpr_reconstruct(inputsig, tempsig, bitcode, constants, input_names):
    return NumExpr(inputsig, tempsig, bitcode, constants, input_names)

# Cython
# ======

def cython_reduce(cf):
    pass

def cython_reconstruct(cf):
    pass
