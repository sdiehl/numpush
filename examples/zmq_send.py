import zmq
from numpy import array
from pandas import DataFrame
#from theano.tensor import Tensor

from numpush.zmq_net import numsend

ctx = zmq.Context.instance()
sock = ctx.socket(zmq.PUSH)
sock.bind('tcp://127.0.0.1:5555')

# ------------------
nd = array([
  [1,2,3],
  [2,3,4],
  [5,8,9],
])
numsend(sock, nd)
# ------------------
df = DataFrame({'a': [1,2,3], 'b': [4,5,6]})
numsend(sock, df)
# ------------------
