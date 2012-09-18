import zmq
import zmq_blosc
from numpy import linspace

ctx = zmq_blosc.BloscContext()

sock = ctx.socket(zmq.PUSH)
sock.bind('tcp://127.0.0.1:5560')

a = linspace(1, 100, 100)
print a.dtype

sock.send(a)
