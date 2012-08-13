from os import getpid

from numpy.random import randn
from numpush.shmem import SDataFrame
from pandas import DataFrame
from multiprocessing import Process

N, M = 10, 10
df  = DataFrame(randn(N,M))
sdf = SDataFrame(df)

assert df == sdf
assert df is not sdf

def modify(shared_df, start):
    # Modify the column of the dataframe with the pid of the process
    # operating on it. It's stupid but it illustrates that the DataFrame
    # is truly shared memory instead of copy-on-write.
    for i in xrange(start, N, 2):
        shared_df[i] = getpid()

# Shared Memory
# =============

p1 = Process(target=modify, args=(sdf,0))
p2 = Process(target=modify, args=(sdf,1))
p1.start()
p2.start()
p1.join()
p2.join()

print sdf.to_string()

# Copy on Write
# =============

p1 = Process(target=modify, args=(df,0))
p2 = Process(target=modify, args=(df,1))
p1.start()
p2.start()
p1.join()
p2.join()

print df.to_string()
