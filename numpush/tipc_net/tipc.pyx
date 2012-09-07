from os import strerror
from libc.sys cimport socket
from libc.stdint cimport uint32_t, uint64_t, ssize_t

cdef extern from "linux/tipc.h":

    enum: TIPC_OK
    enum: TIPC_ERR_NO_NAM
    enum: TIPC_ERR_NO_PORT
    enum: TIPC_ERR_NO_NODE
    enum: TIPC_ERR_OVERLOAD
    enum: TIPC_CONN_SHUTDOWN

    enum: TIPC_ADDR_NAMESEQ
    enum: TIPC_ADDR_NAME
    enum: TIPC_ADDR_ID
    enum: TIPC_ZONE_SCOPE
    enum: TIPC_CLUSTER_SCOPE
    enum: TIPC_NODE_SCOPE
    enum: TIPC_IMPORTANCE
    enum: TIPC_SRC_DROPPABLE
    enum: TIPC_DEST_DROPPABLE
    enum: TIPC_CONN_TIMEOUT
    enum: TIPC_LOW_IMPORTANCE
    enum: TIPC_MEDIUM_IMPORTANCE
    enum: TIPC_HIGH_IMPORTANCE
    enum: TIPC_CRITICAL_IMPORTANCE
    enum: TIPC_SUB_PORTS
    enum: TIPC_SUB_SERVICE
    enum: TIPC_SUB_CANCEL
    enum: TIPC_WAIT_FOREVER
    enum: TIPC_PUBLISHED
    enum: TIPC_WITHDRAWN
    enum: TIPC_SUBSCR_TIMEOUT
    enum: TIPC_CFG_SRV
    enum: TIPC_TOP_SRV

    ctypedef struct tipc_portid:
        uint32_t ref
        uint32_t node

    ctypedef struct tipc_name:
        uint32_t type
        uint32_t instance

    ctypedef struct tipc_name_seq:
        uint32_t type
        uint32_t lower
        uint32_t upper

    ctypedef struct tipc_subscr:
        struct tipc_name_seq seq
        uint32_t timeout
        uint32_t filter
        char usr_handle[8]

    ctypedef struct name:
        struct tipc_name name
        uint32_t domain

    ctypedef union tipc_addr:
        struct tipc_portid id
        struct tipc_name_seq nameseq
        struct name

    ctypedef struct sockaddr_tipc:
        unsigned short family
        unsigned char  addrtype
        signed   char  scope
        union tipc_addr

def tipc_socket(int socket_type, int flags):
	int rc;

    with nogil:
        rc = socket(AF_TIPC, socket_type, flags);

    if rc < 0:
        raise OSError(strerror(rc))
    else:
        return rc
