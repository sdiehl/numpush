import numpy as np
from numpy import byte_bounds
from numpush.shmem_views import sview, SyncNumpy

x = np.arange(0,100)
y = sview(x[:50])
z = sview(x[50:])
a = sview(x[2:98])

xptr = byte_bounds(x)
yptr = byte_bounds(y)
zptr = byte_bounds(y)
aptr = byte_bounds(a)

# Left aligned in memory
assert byte_bounds(x)[0] == byte_bounds(y)[0]

# Right aligned in memory
assert byte_bounds(x)[1] == byte_bounds(z)[1]

# Subset
assert xptr[0] < aptr[0] < aptr[1] < xptr[1]

from numpy import add
s = SyncNumpy(x)
