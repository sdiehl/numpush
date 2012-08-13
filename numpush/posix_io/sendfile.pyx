#from libc.stdio cimport printf
from libc.stdint cimport uint32_t, uint64_t

import os
import sys
from mmap import PAGESIZE

cdef extern from "platform_sendfile.h" nogil:
    ctypedef signed off_t
    ctypedef unsigned size_t
    ctypedef signed ssize_t
    struct sf_hdtr

    ssize_t sendfile_linux(int out_fd, int in_fd, uint64_t *offset, size_t nbytes)
    ssize_t sendfile_bsd(int fd, int s, uint64_t *offset, size_t len, sf_hdtr *hdtr, int flags)

cdef extern from "errno.h" nogil:
    enum: EAGAIN
    #enum: EWOULDBLOCK
    enum: EBADF
    enum: EFAULT
    enum: EINVAL
    enum: EIO
    enum: ENOMEM
    enum: EBUSY

    enum: SF_NODISKIO
    enum: SF_MNOWAIT
    enum: SF_SYNC
    int errno


cdef int _posix_sendfile(int fdout, int fdin, uint64_t *offset, size_t nbytes):

    cdef int sent
    cdef int err
    global errno

    if sys.platform == 'win32':
        raise SystemError("Windows not supported")

    # FreeBSD
    if sys.platform == 'freebsd' or sys.platform == 'darwin':
        with nogil:
            ret = sendfile_bsd(fdout, fdin, offset, nbytes, NULL, 0)

            if ret == -1:
                err = 1
                sent = -errno
                errno = 0
            else:
                err = 0
                sent = ret
        return sent

    ## Linux
    else:
        with nogil:
            ret = sendfile_linux(fdout, fdin, offset, nbytes)

            if ret == -1:
                err = 1
                sent = -errno
                errno = 0
            else:
                err = 0
                sent = ret
        return sent

def posix_sendfile(sock, fd, offset=0, nbytes=PAGESIZE):
    cdef uint64_t c_offset = offset
    cdef size_t c_count = nbytes
    cdef int rc

    rc = _posix_sendfile(sock.fileno(), fd.fileno(), &c_offset, nbytes)

    if rc < 0:
        raise OSError(os.strerror(-rc))
    else:
        return rc
