import zmq
from numpy import array
from pandas import DataFrame
#from theano.tensor import Tensor

from numpush.zmq_net import numrecv

ctx = zmq.Context.instance()
sock = ctx.socket(zmq.PULL)
sock.connect('tcp://127.0.0.1:5555')

# ------------------
nd = numrecv(sock)
assert type(nd) is array
print nd
# ------------------
df = numrecv(sock)
assert type(df) is DataFrame
print df
# ------------------
