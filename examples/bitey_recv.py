import sys
import zmq
from types import ModuleType
from numpush.zmq_net import numrecv

ctx = zmq.Context.instance()
sock = ctx.socket(zmq.PULL)
sock.connect('tcp://127.0.0.1:5555')

module = numrecv(sock)
assert type(module) is ModuleType
assert 'example' in sys.modules

import example
assert example.test(1,2) == 3
