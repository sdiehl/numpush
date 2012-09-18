from libc.stdlib cimport free, malloc

#from cpython.buffer cimport *
from cpython cimport PyBytes_FromStringAndSize, \
    PyObject_GetBuffer, PyBUF_ANY_CONTIGUOUS, \
    PyObject_CheckBuffer, PyBuffer_Release

from zmq.core.error import ZMQError, ZMQBindError

cdef extern from "blosc.h" nogil:
    enum: BLOSC_MAX_OVERHEAD

    int blosc_compress(int clevel, int doshuffle, size_t typesize, size_t nbytes,
                       void *src, void *dest, size_t destsize)
    int blosc_decompress(void *src, void *dest, size_t destsize)
    void blosc_free_resources()
    int blosc_set_nthreads(int nthreads)

ctypedef void zmq_free_fn(void *data, void *hint)

cdef extern from "zmq.h" nogil:
    ctypedef void * zmq_msg_t "zmq_msg_t"
    enum: ENOTSUP
    enum: EINVAL

    void* zmq_init (int io_threads)
    void* zmq_socket (void *context, int type)

    int zmq_msg_init (zmq_msg_t *msg)
    int zmq_msg_init_size (zmq_msg_t *msg, size_t size)
    int zmq_msg_init_data (zmq_msg_t *msg, void *data,
        size_t size, zmq_free_fn *ffn, void *hint)
    int zmq_msg_close (zmq_msg_t *msg)
    int zmq_msg_move (zmq_msg_t *dest, zmq_msg_t *src)
    int zmq_msg_copy (zmq_msg_t *dest, zmq_msg_t *src)
    void *zmq_msg_data (zmq_msg_t *msg)
    size_t zmq_msg_size (zmq_msg_t *msg)

    int zmq_send (void *s, zmq_msg_t *msg, int flags)
    int zmq_recv (void *s, zmq_msg_t *msg, int flags)

    int zmq_bind (void *socket, char *endpoint)
    int zmq_connect (void *socket, char *endpoint)
    int zmq_close (void *socket)

    enum: errno
    char *zmq_strerror (int errnum)
    int zmq_errno()

cdef inline object _recv_copy_blosc(void *handle, object msg, int flags=0):
    cdef zmq_msg_t zmq_msg
    cdef char *data_c = NULL
    cdef Py_ssize_t data_len_c

    with nogil:
        zmq_msg_init (&zmq_msg)
        rc = zmq_recv(handle, &zmq_msg, flags)

    if rc < 0:
        raise ZMQError()

    with nogil:
        data_len_c = zmq_msg_size(&zmq_msg)
        blosc_decompress(zmq_msg_data(&zmq_msg), <void*>data_c,
                data_len_c-BLOSC_MAX_OVERHEAD)
        zmq_msg_close(&zmq_msg)

    zmq_msg_close(&zmq_msg)
    return PyBytes_FromStringAndSize(data_c, data_len_c)

cdef inline object _send_copy_blosc(void *handle, object msg, int flags=0):
    """Send a message on this socket by copying its content."""
    cdef int rc, rc2
    cdef zmq_msg_t data
    cdef char *msg_c
    cdef Py_ssize_t msg_c_len=0

    # -- blosc stuff
    cdef size_t nbytes, cbytes, typesize, size
    cdef int clevel = 8
    cdef int doshuffle = 1

    # -- memoryview
    cdef int mode
    cdef Py_buffer view
    cdef void *view_ptr = NULL

    if not PyObject_CheckBuffer(msg):
        raise TypeError("%r does not provide a buffer interface." % msg)

    flags = PyBUF_ANY_CONTIGUOUS
    PyObject_GetBuffer(msg, &view, flags)

    #msg_c = malloc(view.len+BLOSC_MAX_OVERHEAD)
    msg_c = <char*>&view_ptr
    msg_c_len = < Py_ssize_t>view.len

    # blosc typesize <- memoryview itemsize
    typesize = view.itemsize
    PyBuffer_Release(&view)

    with nogil:
        rc = zmq_msg_init_size(&data, msg_c_len)
        size = zmq_msg_size(&data)

        cbytes = blosc_compress(
            clevel,
            doshuffle,
            typesize,
            size,
            msg_c,
            zmq_msg_data(&data),
            (size+BLOSC_MAX_OVERHEAD)
        )

    if rc != 0:
        raise RuntimeError()

    print "Typesize", typesize
    print 'Compression ratio', ((size-cbytes*1.0)/(size))

    with nogil:
        rc = zmq_send(handle, &data, flags)
        rc2 = zmq_msg_close(&data)
        #free(output)

    if rc < 0 or rc2 != 0:
        raise ZMQError()

cdef class BloscSocket:

    cdef void *handle
    cdef void *ctx

    def __init__(self, context, int socket_type):
        pass

    def __cinit__(self, BloscContext context, int socket_type, *args, **kwrags):
        cdef Py_ssize_t c_handle = context._handle
        cdef void *sock = zmq_socket(<void *>c_handle, socket_type)
        if sock == NULL:
            raise ZMQError()
        else:
            self.handle = sock

    def bind(self, addr):
        cdef int rc
        cdef char* c_addr = addr
        with nogil:
            rc = zmq_bind(self.handle, c_addr)
        if rc != 0:
            raise ZMQError()

    def connect(self, addr):
        cdef int rc
        cdef char* c_addr = addr
        with nogil:
            rc = zmq_connect(self.handle, c_addr)
        if rc != 0:
            raise ZMQError()

    cpdef object send(self, object data, int flags=0, copy=True, track=False):
        if copy:
            return _send_copy_blosc(self.handle, data, flags)
        else:
            raise NotImplementedError

    cpdef object recv(self, int flags=0, copy=True, track=False):
        if copy:
            return _recv_copy_blosc(self.handle, flags)
        else:
            raise NotImplementedError

cdef class BloscContext:

    cdef void *handle

    def __init__(self, int io_threads=1):
        #blosc_set_nthreads(env.CORES)
        blosc_set_nthreads(io_threads)

    def set_nthreads(n):
        blosc_set_nthreads(n)

    def __cinit__(self, int io_threads=1):
        self.handle = zmq_init(io_threads)
        if self.handle == NULL:
            raise ZMQError()

    @property
    def _handle(self):
        return <Py_ssize_t> self.handle

    def socket(self, int socket_type):
        return BloscSocket(self, socket_type)

    def __dealloc__(self):
        blosc_free_resources()

# ----------------------------

Context = BloscContext
Socket  = BloscSocket
__all__ = [ Context, Socket ]
