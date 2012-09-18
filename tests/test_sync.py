from os import getpid

from numpy import arange
from numpush.shmem import RawNumpy
from numpush.shmem_views import SyncNumpy

from multiprocessing import Process

N = 100
arr = RawNumpy(arange(0,N))
b = SyncNumpy(arr)

# Parallel "zipper"
def modify(ar, j):
    for i in xrange(0, N):
        ar[i*j] = ar[-i*j]

# Shared Memory
# =============

p1 = Process(target=modify, args=(b,1))
p2 = Process(target=modify, args=(b,-1))
p1.start()
p2.start()
p1.join()
p2.join()

print arr
