import os
import sys
import atexit

from libc.stdint cimport uint32_t, uint64_t
from libc.stdlib cimport malloc, free
from libc.stdio cimport printf
from posix.unistd cimport pipe, close

from mmap import PAGESIZE

from iothread import IOThread

cdef extern from "pthread.h" nogil:
    enum: PTHREAD_CANCEL_ASYNCHRONOUS
    ctypedef unsigned long int pthread_t
    ctypedef union pthread_attr_t:
        char __size[56]
        long int __align
    int pthread_create(pthread_t *thread, pthread_attr_t *attr,
         void *(*start_routine) (void *), void *arg)
    int pthread_setcanceltype(int type, int *oldtype)

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
        sts = splice(fd_in, NULL, fd_out, NULL, nbytes, flags)

        if sts == -1:
            err = 1
            sent = -errno
            errno = 0
        else:
            err = 0
            sent = sts

    return sent

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
    cdef int rc
    global errno

    rc = splice(fd_in, NULL, fd_out, NULL, nbytes, flags)
    free(pms);

    return NULL

# Spin a raw OS thread (no GIL!) to do background continuous data
# transfer between two file descriptors. The POSIX thread also
# shares the same file descriptor as the Python process so we
# have to be a bit careful
def posix_splice_thread(fd1, fd2, fd1_offset=0, fd2_offset=0,
        nbytes=PAGESIZE, flags=SPLICE_F_MOVE):

    if type(fd1) is not int:
        fd1 = fd1.fileno()

    if type(fd2) is not int:
        fd2 = fd2.fileno()

    # TODO: assert that one of these is a pipe. Otherwise we
    # need to set up a loop to relay the data through a pipe

    cdef pthread_t thread
    cdef spliceinfo *pms = <spliceinfo*>malloc(sizeof(spliceinfo))
    pms.fd1 = fd1
    pms.fd2 = fd2
    pms.fd1_offset = fd1_offset
    pms.fd2_offset = fd2_offset
    pms.nbytes = nbytes
    pms.flags = flags

    cdef int retval

    with nogil:
        pthread_create(&thread, NULL , pthread_splice, <void*>pms)
        pthread_setcanceltype(PTHREAD_CANCEL_ASYNCHRONOUS, NULL)

    io = IOThread(thread, fd1, fd2)
    atexit.register(io.ensure)
    return io

def posix_splice_fork(fd1, fd2, fd1_offset=0, fd2_offset=0,
        nbytes=PAGESIZE, flags=SPLICE_F_MOVE):
    if type(fd1) is not int:
        fd1 = fd1.fileno()

    if type(fd2) is not int:
        fd2 = fd2.fileno()

    pid = os.fork()

    if pid == 0:
        rc = splice(fd1, NULL, fd2, NULL, nbytes, flags)
        if rc == 0:
            sys.exit(0)
        else:
            sys.stderr.write('splice failed')
            sys.exit(1)
    else:
        return pid

cdef long splice_chunk(int pipe_fd, int fd_out, size_t nbytes, int flags):
    # Splice from the pipe until the data is depeleted

    cdef int calls = 0
    cdef long written = 1
    cdef long total = 0

    while written > 0:
        written = splice(pipe_fd, NULL, fd_out, NULL, nbytes, flags)

        if written < 0:
            raise IOError("Couldn't splice")

        calls += 1
        total += written

    return (total, calls)

cdef long splice_sockets(int sock1, int sock2, int flags):
    #                 Unix Pipe
    #           +-------------------+
    # sock1 => fd[0] => Splice => fd[1] => sock2

    # Splice two sockets using the splice() calls using an
    # intermediary unix pipe.

    # A unix pipe is ostensibly a in-kernel buffer between two arbitrary
    # points so we still maintain zero-copy like behavior.

    cdef int pipefd[2]
    cdef uint64_t *start = <uint64_t*>0
    cdef size_t size = 8194

    cdef unsigned int status = 0
    cdef unsigned long copied = 0
    cdef ssize_t nr
    cdef int ret
    cdef int rc

    rc = pipe(pipefd)

    flags |= SPLICE_F_MORE | SPLICE_F_MOVE

    while 1:
        nr = splice(sock1, NULL, pipefd[1], NULL, size, flags)
        if nr <= 0:
            ret = nr
            #break
        while nr:
            ret = splice(pipefd[0], NULL, sock2, NULL, nr, flags)
            if ret <= 0:
                break
            nr -= ret

    close(pipefd[0])
    close(pipefd[1])
    return ret

def posix_splice_sockets(fd1, fd2, flags=0):
    if type(fd1) is not int:
        fd1 = fd1.fileno()

    if type(fd2) is not int:
        fd2 = fd2.fileno()

    cdef int c_flags = flags

    rc = splice_sockets(fd1, fd2, flags)

    if rc < 0:
        raise OSError(os.strerror(errno))
    return rc
