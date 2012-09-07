numpush
=======

Efficient distribution for scientific Python data structures and code.

Numpush is not a clustering or map-reduce solution, it is merely
a library of common functions that are often needed when building
distributed scientific Python applications.


Target Infastructure
--------------------

* Libraries
    * numpy
    * pandas
    * numba
    * bitey
    * llvm-py
    * theano
    * numexpr
    * hdf5
    * carray
* Datastore Backends
    * MooseFS
    * Redis
* Network transports
    * TIPC
    * ZeroMQ
    * TCP
* IO Operations
    * sendfile
    * splice
    * mmap
    * read/write

Note: This is indication of the direction of the project, quite a
bit of it is incomplete at this time.

Data
----

The core idea is based on the observation that most scientific Python
data structures can be represented by two parts:

1. Large block of indexable memory
2. Small bits of metadata

(1) is a heavy object to move around, so we use fast transports (i.e.
ZeroMQ, TIPC ) that all act on a universal memoryview
interface doing low-level POSIX IO calls ( mmap, splice, sendfile )
that don't require needless copying in userspace to send data and
can delegate scheduling to the Linux kernel.

(2) are trivial to move around, these are pickled or msgpacked and moved
around easily since they are most often PyObject's or can be encoded as
PyObjects.

For example a Pandas dataframe is a Numpy array with some extra
metadata and logical methods. The logic exists wherever the library is
installed, to the move the dataframe we need then only encode
the metadata and buffer the internal array.

```python
>>> df = DateFrame({'a': [1,2,3], 'b': [4,5,6]})
   a  b
0  1  4
1  2  5
2  3  6

>>> index = df.index.tolist()
>>> columns = df.columns.tolist()
>>> dtype = df.values.dtype
>>> shape = df.values.shape

>>> nd = buffer(df.values)

... sent over the wire ..

>>> nd2 = np.frombuffer(nd, dtype=dtype).reshape(shape)

>>> df2 = DataFrame(nd2, index=index, columns=columns)
```

Code
----

The code scenario is slightly different, but usually the idea
is that we have

1. Chunk of bytecode/bitcode that is moveable between homogeneous computational architectures.
2. Some associated "state" that is needed to bootstrap the code

(1) is most often simply a string buffer and moving them around the
network is trivial. Quite often (2) does not ever occur since we are
just moving pure objects around.

For example a slug of Numba LLVM that does some simple numerical
operations, like:

```llvm
define i32 @myfunc(i32, i32, i32) {
        %3 = add i32 %0, %1
        %4 = mul i32 %3, %2
        ret i32 %4
}
```
Can easily be serialized over the network, recompile at the
target and translated into a Numpy ufunc by the Numba
infrastructure.

```python
'BC\xc0\xde!\x0c\x00\x00z\x00\x00\x00\x01\x10\x00\x00\x12\x00\x00\x00\x07\x81#\x91A'
```

Shared Memory
-------------

Once data is at a remote target one often wants to farm it out to as
many cores (i.e. through multiprocessing ) as possible all with the
same shared memory source. For numpy derivative data structures this is
not difficult ( though very undocumented! ). To that end there are some
*simple* shared memory methods included for doing *simple* shared memory
array operations with mutex.

For example one might want a shared memory-backed DataFrame and to work
on it across 8 cores.

This could be done with ctypes hacks on ``multiprocessing.RawArray``,
but they were ugly hacks. The ``numpush.shmem`` module has a cleaner
implementation.


```python
from multiprocessing import Pool
from numpush.shmem import SDataFrame

df = SDataFrame(.. your enormous dataframe .. )

def f(df):
    ... modify shared memory dataframe ...

pool = Pool(processes=8)
pool.apply(f, df)
pool.join()
```

Data Stores
-----------

Not going to try and solve the problem of distributed fault-tolerant
datastores, both MooseFS and Redis work nearly out of the box and can
address most use cases. The goal is simply to make them
interface with scientific Python libraries more easily.

MooseFS is distributed, fault-tolerant and quite easy to
bootstrap on small-medium size clusters, especially on EC2. Works
well with data that can be manipulated as file-like objects.

Redis is local, fast, simple, and with hiredis can work efficiently with
large buffers. Works well for small data simple data that fits
into key-value model.

Required
--------

* libzmq
* Python 2.7.x ( memoryview is used copiously )
* pyzmq 2.1.11
* msgpack
* Cython 0.16

Optional
* https://github.com/techhat/python-moosefs
* redis & hiredis

License
-------

Released under the MIT license.

```
Copyright (c) 2012 Stephen Diehl, <stephen.m.diehl@gmail.com>
See LICENSE and NOTICE for details.
```
