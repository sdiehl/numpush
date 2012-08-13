import socket
import numpy as np
import os.path as path
from tempfile import mkdtemp
from numpush.posix_io.sendfile import posix_sendfile

# Just vanilla TCP over IPV4
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect(("127.0.0.1", 8000))

filename = path.join(mkdtemp(), 'map')
data = np.linspace(0, 1000)

fd = open(filename, 'a+')
fp = np.memmap(filename, dtype=data.dtype, shape=data.shape)
fp[:] = data[:]

sent = posix_sendfile(sock, fd, nbytes=1024)
assert sent == data.nbytes
