import server
import threading
import os
import sys
import resource

# class createDaemon:
#
#     UMASK = 0
#     WORKDIR = "/Users/jfourne/Learning/Python/Taskmaster/rendu"
#     MAXFD = 1024
#
#     if(hasattr(os, "devnull")):
#         REDIRECT_TO = os.devnull
#     else:
#         REDIRECT_TO = "/dev/null"
#
#     def __init__(self):
#
#         try:
#             pid = os.fork()
#         except OSError:
#             raise Exception
#
#         if pid == 0:
#             os.setsid()
#             try:
#                 pid = os.fork
#             except OSError:
#                 raise Exception
#             if pid == 0:
#                 os.chdir(WORKDIR)
#                 os.umask(UMASK)
#             else:
#                 os._exit(0)
#         else:
#             os._exit(0)

def createDaemon():
    UMASK = 0
    WORKDIR = os.getcwd()
    MAXFD = 1024
    REDIRECT_TO = "/dev/null"


    try:
        pid = os.fork()
    except OSError as e:
        print(e)
        raise
    if pid == 0:
        os.setsid()
        try:
            pid = os.fork()
        except OSError as e:
            print(e)
            raise
        if pid == 0:
            os.chdir(WORKDIR)
            os.umask(UMASK)
        else:
            os._exit(0)
    else:
        os._exit(0)
    maxfd = resource.getrlimit(resource.RLIMIT_NOFILE)[1]
    if (maxfd == resource.RLIM_INFINITY):
      maxfd = MAXFD
    for fd in range(0, maxfd):
        try:
            os.close(fd)
        except OSError:
            pass
    os.open(REDIRECT_TO, os.O_RDWR)
    os.dup2(0, 1)
    os.dup2(0, 2)
    return (0)

if __name__ == '__main__':

    pgid = os.getpgid(0)
    print(str(pgid))
    retCode = createDaemon()
    server.Server('127.0.0.1', 12800, pgid).listen()
    sys.exit(retCode)
