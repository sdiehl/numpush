#if !defined(__APPLE__)     && \
    !defined(__FreeBSD__)   && \
    !defined(__linux__)
#error invalid platform
#endif

#include <sys/uio.h>

struct sf_hdtr {
    struct iovec *headers;
    int hdr_cnt;
    struct iovec *trailers;
    int trl_cnt;
};

#if defined(__FreeBSD__)
#include <sys/types.h>
#include <sys/socket.h>
#define sendfile_bsd sendfile
#define sendfile_linux (void *)
#endif

#if defined(__linux__)
#include <sys/sendfile.h>
#define sendfile_bsd (void *)
#define sendfile_linux sendfile
#endif
