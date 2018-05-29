import socket
import threading
import sys
import time
import os
import signal
import configurationClass as Conf
from threading import Thread

class Server:

    host = str()
    port = int()
    program_dict = {}
    arg_all = False
    current_client = 0
    pgid = 0
    conf = Conf.ConfigurationFile()

    def __init__(self, host, port, pgid=-1):

        self.host = host
        self.port = port
        self.pgid = pgid
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind((host, port))
        for program in self.conf.parsed_file['programs']:
            message_list = []
            self.program_dict[program] = {}
            self.program_dict[program]['status'] = 'STOPPED'
            message_list.append(program)
            self.multipleAction(message_list, self.start)

    def start(self, program, print_message=True):
        self.execute(self.conf.parsed_file['programs'], program, print_message)
        return

    def stop(self, program):
        if self.program_dict[program]['status'] == 'RUNNING':
            stopwaitsecs = float(self.conf.parsed_file['programs'][program].get('stopwaitsecs', 10))
            stopsignal = self.conf.parsed_file['programs'][program].get('stopsignal', "TERM")
            if stopsignal == "TERM":
                os.kill(self.program_dict[program]['pid'], signal.SIGTERM)
            elif stopsignal == "HUP":
                os.kill(self.program_dict[program]['pid'], signal.SIGHUP)
            elif stopsignal == "INT":
                os.kill(self.program_dict[program]['pid'], signal.SIGINT)
            elif stopsignal == "QUIT":
                os.kill(self.program_dict[program]['pid'], signal.SIGQUIT)
            elif stopsignal == "KILL":
                os.kill(self.program_dict[program]['pid'], signal.SIGKILL)
            elif stopsignal == "USR1":
                os.kill(self.program_dict[program]['pid'], signal.SIGUS1)
            elif stopsignal == "USR2":
                os.kill(self.program_dict[program]['pid'], signal.SIGUSR2)
            stopped = False
            curr_time = time.time()
            while (time.time() < curr_time + stopwaitsecs and stopped == False):
                if self.program_dict[program]['status'] == 'STOPPED':
                    stopped = True
            if stopped == False:
                os.kill(self.program_dict[program]['pid'], signal.SIGKILL)
        else:
            if self.arg_all == False:
                self.current_client.send("{}: ERROR (not running)\n".format(program).encode('utf-8'))
                print("{}: ERROR (not running)".format(program))
        return

    def restart(self, message_list):
        self.stop(message_list)
        self.start(message_list)

    def printStatus(self, program):
        if len(self.program_dict[program]) == 1:
            return ("{}       {}\n".format(program, self.program_dict[program]['status']))
            print("{}       {}".format(program, self.program_dict[program]['status']))
        elif self.program_dict[program]['status'] == 'RUNNING':
            return ("{}       {}  pid {}, uptime {}\n".format(program, self.program_dict[program]['status'], self.program_dict[program]['pid'], time.strftime("%H:%M:%S", time.gmtime(time.time() - self.program_dict[program]['detail']))))
            print("{}       {}  pid {}, uptime {}".format(program, self.program_dict[program]['status'], self.program_dict[program]['pid'], time.strftime("%H:%M:%S", time.gmtime(self.program_dict[program]['detail']))))
        elif self.program_dict[program]['status'] == 'STARTING':
            return ("{}       {}\n".format(program, self.program_dict[program]['status']))
            print("{}       {}".format(program, self.program_dict[program]['status']))
        else:
            return ("{}       {}  {}\n".format(program, self.program_dict[program]['status'], self.program_dict[program]['detail']))
            print("{}       {}  {}".format(program, self.program_dict[program]['status'], self.program_dict[program]['detail']))

    def status(self, program):
        response = []
        if program == '':
            for key in self.program_dict.keys():
                response.append(self.printStatus(key))
            self.current_client.send(''.join(response).encode('utf-8'))
        else:
            self.current_client.send(self.printStatus(program).encode('utf-8'))

    def multipleAction(self, message_list, action):

        if (len(message_list) == 0):
            return
        else:
            if message_list[0] in self.program_dict.keys():
                multi_process = Thread(target=action, args=(message_list[0],))
                multi_process.start()
            else:
                self.current_client.send("{}: ERROR (no such process)\n".format(message_list[0]).encode('utf-8'))
                print("{}: ERROR (no such process)".format(message_list[0]))
            del message_list[0]
            self.multipleAction(message_list, action)

    def redirectMessage(self, message):

        message_list = message.split(" ")
        if (len(message_list) == 1):
            if (message_list[0] == 'status'):
                self.status('')
                return
            elif(message_list[0] == 'reload'):
                # self.reload()
                return
        else:
            if (message_list[0] == 'start'):
                action = self.start
            elif (message_list[0] == 'stop'):
                action = self.stop
            elif (message_list[0] == 'restart'):
                action = self.restart
            else:
                action = self.status
            if (message_list[0] == 'reload'):
                self.current_client.send(b"Error: Too many argument\n")
                print('Error: Too many argument')
                return
            del message_list[0]
            if message_list[0] == 'all' and len(message_list) != 1 and action != self.status:
                self.current_client.send(b"Error: Too many argument\n")
                print('Error: Too many argument')
                return
            if message_list[0] == 'all' and action == self.status:
                self.current_client.send(b"Error: Too many argument\n")
                print('Error: Too many argument')
                return
            if (message_list[0] == 'all'):
                self.arg_all = True
                message_list = []
                for key in self.program_dict.keys():
                    message_list.append(key)
            self.multipleAction(message_list, action)
            self.arg_all = False

    def receiveMsg(self, client, address):

        buff = 1024
        self.current_client = client
        self.status('')
        message = b""
        while message != b"shutdown":
            try:
                message = client.recv(buff)
                # self.current_client = client
                if message:
                    print("Received: ", message.decode())
                else:
                    #
                    # A CHECK CAR error n'existe pas
                    #
                    raise error('Client disconnected')
                self.redirectMessage(message.decode())
            except:
                self.closeCo(client)
                return False
        self.redirectMessage("stop all")
        self.current_client.send("Server stopped\n".encode('utf-8'))
        self.sock.close()

    def listen(self):

        try:
            self.sock.listen(5)
            print("Server is listening on port {}" .format(self.port))
        except:
            print("Error: server can't listen on port {}" .format(self.port))
            return
        while True:
            try:
                client_connexion, data_connexion = self.sock.accept()
                print("Accepted a new connexion: {0} on port {1}" .format(data_connexion[0], data_connexion[1]))
                thread = threading.Thread(target=self.receiveMsg, args=(client_connexion, data_connexion))
                thread.start()
            except:
                print('Error: an error occured during acceptation of new client')
                self.sock.close()
                return

    def closeCo(self, client):
        client.close()

    def execute(self, programs_list, program, print_message=True):
        if self.program_dict[program]['status'] == 'RUNNING' or self.program_dict[program]['status'] == 'STARTING':
            if self.arg_all == False:
                self.current_client.send("{}: ERROR (Already started)\n".format(program).encode('utf-8'))
                print("{}: ERROR (Already started)".format(program))
            return
        child = self.createChild()
        if child != -1:
            if child > 0:
                starting = True
                # curr_time = time.time()
                # while (time.time() < curr_time + float(3)):
                #     try:
                #     except:
                #         starting = False
                #         self.program_dict[program][0] = 'BACKOFF'
                # self.program_dict[program][0] = 'STOPPED'
                # del self.program_dict[program][1]
                # print(str(pid), str(status), str(starting))
                self.program_dict[program] = {}
                self.program_dict[program]['status'] = 'STARTING'
                curr_time = time.time()
                self.program_dict[program]['detail'] = curr_time
                startsecs = float(self.conf.parsed_file['programs'][program].get('startsecs', '3'))
                found_exit = False
                while (time.time() < curr_time + startsecs and starting == True):
                    try:
                        pid, status = os.waitpid(child, os.WNOHANG)
                    except:
                        starting = False
                        self.program_dict[program]['status'] = 'BACKOFF'
                        self.program_dict[program]['detail'] = "Exited too quickly (process log may have details)"
                        if self.current_client != 0:
                            self.current_client.send("{}: ERROR (spawn error)".format(program).encode('utf-8'))
                        print("{}: ERROR (spawn error)".format(program))
                print(str(pid), str(status), str(starting))
                if starting == True:
                    self.program_dict[program]['status'] = 'RUNNING'
                    self.program_dict[program]['pid'] = child
                    if print_message == True and self.current_client != 0:
                        self.current_client.send("{}: started\n".format(program).encode('utf-8'))
                    print("{}: started".format(program))
                    try:
                        pid, status = os.waitpid(child, 0)
                        self.program_dict[program] = {}
                        self.program_dict[program]['status'] = 'STOPPED'
                        if self.current_client != 0:
                            self.current_client.send("{}: stopped\n".format(program).encode('utf-8'))
                        print("{}: stopped".format(program))
                    except OSError as message:
                        print(message)
                autorestart = self.conf.parsed_file['programs'][program].get('autorestart', 'unexpected')
                if autorestart == 'false':
                    found_exit = True
                if autorestart == 'unexpected':
                    exitcodes = self.conf.parsed_file['programs'][program]['exitcodes'].split(',')
                    for exitcode in exitcodes:
                        if str(status) == str(exitcode):
                            found_exit = True
                # if starting == False:
                #     found_exit = False
                # if found_exit == False and int(self.conf.parsed_file['programs'][program]['startretries']) > 0:
                #     self.conf.parsed_file['programs'][program]['startretries'] -= 1
                #     self.start(program, print_message=False)
                # if self.conf.parsed_file['programs'][program]['startretries'] == 0:
                #     self.program_dict[program]['status'] = 'FATAL'
                #     self.program_dict[program]['detail'] = 'Exited too quickly (process log may have details)'

                return
            if child == 0:
                try:
                    fd1 = os.open('log.log', os.O_RDWR | os.O_CREAT | os.O_APPEND)
                    os.dup2(fd1, 1)
                except OSError as e:
                    self.current_client.send("{}\n".format(e).encode('utf-8'))
                    print(e)
                    os._exit(0)
                try:
                    fd2 = os.open('err.log', os.O_RDWR | os.O_CREAT | os.O_APPEND)
                    os.dup2(fd2, 2)
                except OSError as e:
                    self.current_client.send("{}\n".format(e).encode('utf-8'))
                    print(e)
                    os._exit(0)
                # try:
                #     os.dup2(sys.stdin, 0)
                # except OSError as e:
                #     self.current_client.send("{}\n".format(e).encode('utf-8'))
                #     print(e)
                #     os._exit(0)

                if self.pgid != -1:
                    try:
                        os.setpgid(0, self.pgid)
                    except OSError as e:
                        print(e)
                try:
                    args = programs_list[program]['command'].split(" ")
                    os.execv(args[0], args)
                except OSError as msg:
                    print(msg)
                os.close(fd1)
                os.close(fd2)
                os._exit(0)

    def createChild(self):
        child_pid = os.fork()
        return child_pid

if __name__ == '__main__':

    new_server = Server('127.0.0.1', 12800).listen()
