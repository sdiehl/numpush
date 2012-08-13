import zmq
from llvm.core import Module
from llvm.ee import ExecutionEngine

from numpush.zmq_net import numsend

import bitey
example = bitey.load_library('./example')

ctx = zmq.Context.instance()
sock = ctx.socket(zmq.PUSH)
sock.bind('tcp://127.0.0.1:5555')

numsend(sock, example)
