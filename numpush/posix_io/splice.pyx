import os
from libc.stdint cimport uint32_t, uint64_t
from libc.stdlib cimport malloc

# Shuould be identical to sysconf(_SC_PAGESIZE)
from mmap import PAGESIZE

cdef extern from "pthread.h" nogil:
    ctypedef unsigned long int pthread_t
    ctypedef union pthread_attr_t:
        char __size[56]
        long int __align

    int pthread_create(pthread_t *thread, pthread_attr_t *attr,
                             void *(*start_routine) (void *), void *arg)
    int pthread_tryjoin_np (pthread_t __th, void **__thread_return)
    int pthread_cancel (pthread_t __th)

cdef extern from "fcntl.h" nogil:
    ctypedef unsigned size_t
    ctypedef signed ssize_t

    ssize_t splice(int fd_in, uint64_t *off_in, int fd_out, uint64_t *off_out,
            size_t len, unsigned int flags)

    enum: SPLICE_F_MOVE
    enum: SPLICE_F_NONBLOCK
    enum: SPLICE_F_MORE
    enum: SPLICE_F_GIFT

cdef extern from "errno.h" nogil:
    enum: SF_NODISKIO
    enum: SF_MNOWAIT
    enum: SF_SYNC
    int errno

cdef extern from "Python.h" nogil:
    ctypedef struct PyThreadState
    void PyEval_InitThreads()
    PyThreadState* PyEval_SaveThread
    void PyEval_RestoreThread(PyThreadState *tstate)

ctypedef struct spliceinfo:
    int fd1
    int fd2
    uint64_t fd1_offset
    uint64_t fd2_offset
    size_t nbytes
    int flags

SPLICE_MOVE = SPLICE_F_MOVE
SPLICE_NONBLOCK = SPLICE_F_NONBLOCK
SPLICE_MORE = SPLICE_F_MORE
SPLICE_GIFT = SPLICE_F_GIFT

cdef int _posix_splice(int fd_in, uint64_t *off_in, int fd_out,
        uint64_t *off_out, size_t nbytes, unsigned int flags):
    cdef int sent
    cdef int err
    global errno

    cdef uint64_t a = 0
    cdef uint64_t b = 0

    # If fd_in is a pipe then off_in must be NULL
    with nogil:
        sts = splice(fd_in, NULL, fd_out, NULL, 1024, 0)

        if sts == -1:
            err = 1
            sent = -errno
            errno = 0
        else:
            err = 0
            sent = sts

    return sent

# Changed the signature a bit to match our common use case of 0, 0
# offsets. If you need SPLICE_F_MORE then you probably just want
# to use the sendfile implementation.
def posix_splice(fd1, fd2, fd1_offset=0, fd2_offset=0,
        nbytes=PAGESIZE, flags=SPLICE_F_MOVE):

    if type(fd1) is int:
        fd1 = os.fdopen(fd1, 'r')

    if type(fd2) is int:
        fd2 = os.fdopen(fd2, 'w')

    cdef uint64_t c_fd1offset = fd1_offset
    cdef uint64_t c_fd2offset = fd2_offset
    cdef size_t c_count = nbytes
    cdef int c_flags = flags
    cdef int rc

    rc = _posix_splice(
        fd1.fileno(),
        &c_fd1offset,
        fd2.fileno(),
        &c_fd2offset,
        nbytes,
        0
    )

    if rc < 0:
        print -rc
        raise OSError(os.strerror(-rc))
    else:
        return rc

cdef void* pthread_splice(void *p) nogil:
    # cython *grumble grumble*
    cdef spliceinfo *pms = <spliceinfo*>(p)
    cdef int fd_in = pms.fd1
    cdef int fd_out = pms.fd2
    cdef uint64_t fd1_offset = pms.fd1_offset
    cdef uint64_t fd2_offset = pms.fd2_offset
    cdef size_t nbytes = pms.nbytes
    cdef int flags = pms.flags

    splice(fd_in, NULL, fd_out, NULL, 1024, 0)
    return NULL

# Spin a raw OS thread (no GIL!) to do background continuous data
# transfer between two file descriptors. The POSIX thread also
# shares the same file descriptor as the Python process so we
# have to be a bit careful
cdef void _spawn(int fd1, int fd2, uint32_t fd1_offset, uint32_t fd2_offset, int nbytes, int flags):
    #cython *grumble grumble*
    cdef pthread_t thread
    cdef spliceinfo *pms = <spliceinfo*>malloc(sizeof(spliceinfo))

    pms.fd1 = fd1
    pms.fd2 = fd2
    pms.fd1_offset = 0
    pms.fd2_offset = 0
    pms.nbytes = nbytes
    pms.flags = flags

    with nogil:
        pthread_create(&thread, NULL , pthread_splice, <void*>pms)

def posix_splice_thread(fd1, fd2, fd1_offset=0, fd2_offset=0,
        nbytes=PAGESIZE, flags=SPLICE_F_MOVE):

    if type(fd1) is int:
        fd1 = os.fdopen(fd1, 'r')

    if type(fd2) is int:
        fd2 = os.fdopen(fd2, 'w')

    cdef uint64_t c_fd1offset = fd1_offset
    cdef uint64_t c_fd2offset = fd2_offset

    cdef size_t c_count = nbytes
    cdef int c_flags = flags
    cdef int rc

    cdef int c_fd1 = fd1.fileno()
    cdef int c_fd2 = fd2.fileno()

    _spawn(
        c_fd1,
        c_fd1offset,
        c_fd2,
        c_fd2offset,
        c_count,
        c_flags
    )
    return -1
