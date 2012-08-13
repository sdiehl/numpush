import os
from libc.stdint cimport uint32_t, uint64_t
from mmap import PAGESIZE

cdef extern from "fcntl.h" nogil:
    ctypedef unsigned size_t
    ctypedef signed ssize_t

    ssize_t splice(int fd_in, uint64_t *off_in, int fd_out, uint64_t *off_out, size_t len, unsigned int flags)

    enum: SPLICE_F_MOVE
    enum: SPLICE_F_NONBLOCK
    enum: SPLICE_F_MORE
    enum: SPLICE_F_GIFT

cdef extern from "errno.h" nogil:
    enum: SF_NODISKIO
    enum: SF_MNOWAIT
    enum: SF_SYNC
    int errno

cdef int _posix_splice(int fd_in, uint64_t *off_in, int fd_out, uint64_t *off_out, size_t nbytes, unsigned int flags):
    cdef int sent
    cdef int err
    global errno

    with nogil:
        sts = splice(fd_in, off_in, fd_out, off_out, nbytes, flags)

        if sts == -1:
            err = 1
            sent = -errno
            errno = 0
        else:
            err = 0
            sent = sts
    return sent

# Changed the signature a bit to match our common use case of 0,0
# offsets
def posix_splice(fd1, fd2, fd1_offset=0, fd2_offset=0, nbytes=PAGESIZE, flags=0):

    if type(fd1) is int:
        fd1 = os.fdopen(fd1, 'r')

    if type(fd2) is int:
        fd2 = os.fdopen(fd2, 'w')

    cdef uint64_t c_fd1offset = fd1_offset
    cdef uint64_t c_fd2offset = fd2_offset
    cdef size_t c_count = nbytes
    cdef int c_flags = flags
    cdef int rc

    rc = _posix_splice(fd1.fileno(), &c_fd1offset, fd2.fileno(), &c_fd2offset, nbytes, 0)

    if rc < 0:
        raise OSError(os.strerror(-rc))
    else:
        return rc
