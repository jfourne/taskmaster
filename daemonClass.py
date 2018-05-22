import server
import threading
import os

class createDaemon:

    UMASK = 0
    WORKDIR = "/Users/robechon/Taskmaster"
    MAXFD = 1024
    
    if(hasattr(os, "devnull")):
        REDIRECT_TO = os.devnull
    else:
        REDIRECT_TO = "/dev/null"

    def __init__(self):
        
        try:
            pid = os.fork()
        except OSError, e:
            raise Exception, "%s [%d]" % (e.strerror, e.errno)
       
        if pid == 0:
            os.setsid()
            try:
                pid = os.fork
            except OSError, e:
                raise Exception, "%s [%d]" % (e.strerror, e.errno)
            if pid == 0:   
                os.chdir(WORKDIR)
                os.umask(UMASK)
            else:
                os._exit(0)
        else:
            os._exit(0)


if __name__ == '__main__':

    retCode = createDaemon()
    while True:
        server.Server('127.0.0.1', 12800).listen()
