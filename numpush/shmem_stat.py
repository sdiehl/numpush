def shm_counters():
    f = open("/proc/sysvipc/shm", "r")
    try:
        lines = f.readlines()
    finally:
        f.close()

    retdict = {}
    for line in lines[2:]:
        fields = line.split()
        shmid   = int(fields[1])
        perms   = int(fields[2])
        size    = int(fields[3])
        cpid    = int(fields[4])
        lpid    = int(fields[5])
        nattach = int(fields[6])
        swap    = int(fields[11])

        retdict[shmid] = (perms, size, cpid, lpid, nattach, swap)
    return retdict
