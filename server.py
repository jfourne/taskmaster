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
    conf = Conf.ConfigurationFile()

    def __init__(self, host, port):

        self.host = host
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind((host, port))
        for program in self.conf.parsed_file['programs']:
            self.program_dict[program] = ['STOPPED']

    def start(self, program):
        self.execute(self.conf.parsed_file['programs'], program)
        return

    def stop(self, program):
        if self.program_dict[program][0] == 'RUNNING':
            #
            # SLEEP EST POUR LORSQUE LE PROGRAMME NE S ARRETE TOUJOURS PAS
            #
            time.sleep(float(self.conf.parsed_file['programs'][program].get('stopwaitsecs', 10)))
            stopsignal = self.conf.parsed_file['programs'][program].get('stopsignal', "TERM")
            if stopsignal == "TERM":
                os.kill(self.program_dict[program][1], signal.SIGTERM)
            elif stopsignal == "HUP":
                os.kill(self.program_dict[program][1], signal.SIGHUP)
            elif stopsignal == "INT":
                os.kill(self.program_dict[program][1], signal.SIGINT)
            elif stopsignal == "QUIT":
                os.kill(self.program_dict[program][1], signal.SIGQUIT)
            elif stopsignal == "KILL":
                os.kill(self.program_dict[program][1], signal.SIGKILL)
            elif stopsignal == "USR1":
                os.kill(self.program_dict[program][1], signal.SIGUS1)
            elif stopsignal == "USR2":
                os.kill(self.program_dict[program][1], signal.SIGUSR2)
            self.current_client.send("{}: stopped".format(program).encode('utf-8'))
            print("{}: stopped".format(program))
        else:
            if self.arg_all == False:
                self.current_client.send("{}: ERROR (not running)".format(program).encode('utf-8'))
                print("{}: ERROR (not running)".format(program))
        return

    def restart(self, message_list):
        self.stop(message_list)
        self.start(message_list)

    def printStatus(self, program):
        if len(self.program_dict[program]) == 1:
            return ("{}       {}".format(program, self.program_dict[program][0]))
            print("{}       {}".format(program, self.program_dict[program][0]))
        else:
            return ("{}       {}  pid {}".format(program, self.program_dict[program][0], self.program_dict[program][1]))
            print("{}       {}  pid {}".format(program, self.program_dict[program][0], self.program_dict[program][1]))

    def status(self, program):
        response = []
        if program == '':
            for key in self.program_dict.keys():
                response.append(self.printStatus(key))
            self.current_client.send('\n'.join(response).encode('utf-8'))
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
                self.current_client.send("{}: ERROR (no such process)".format(message_list[0]).encode('utf-8'))
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
                self.current_client.send(b"Error: Too many argument")
                print('Error: Too many argument')
                return
            del message_list[0]
            if message_list[0] == 'all' and len(message_list) != 1 and action != self.status:
                self.current_client.send(b"Error: Too many argument")
                print('Error: Too many argument')
                return
            if message_list[0] == 'all' and action == self.status:
                self.current_client.send(b"Error: Too many argument")
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
        message = b""
        while message != b"shutdown":
            try:
                message = client.recv(buff)
                self.current_client = client
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

    def execute(self, programs_list, program):
        if self.program_dict[program][0] == 'RUNNING':
            if self.arg_all == False:
                self.current_client.send("{}: ERROR (Already started)".format(program).encode('utf-8'))
                print("{}: ERROR (Already started)".format(program))
            return
        child = self.createChild()
        if child != -1:
            if child > 0:
                self.program_dict[program][0] = 'RUNNING'
                self.program_dict[program].append(child)
                self.current_client.send("{}: started".format(program).encode('utf-8'))
                print("{}: started".format(program))
                try:
                    pid, status = os.waitpid(child, 0)
                    self.program_dict[program][0] = 'STOPPED'
                    del self.program_dict[program][1]
                    found_exit = False
                    autorestart = self.conf.parsed_file['programs'][program].get('autorestart', 'unexpected')
                    if autorestart == 'false':
                        found_exit = True
                    if autorestart == 'unexpected':
                        exitcodes = self.conf.parsed_file['programs'][program]['exitcodes'].split(',')
                        for exitcode in exitcodes:
                            if str(status) == str(exitcode):
                                found_exit = True
                    # if found_exit == False:
                    #     self.start(program)

                except OSError as message:
                    print(message)
                return
            if child == 0:
                try:
                    args = programs_list[program]['command'].split(" ")
                    os.execv(args[0], args)
                except OSError as msg:
                    print(msg)
                os._exit(0)

    def createChild(self):
        child_pid = os.fork()
        return child_pid

if __name__ == '__main__':

    new_server = Server('127.0.0.1', 12800).listen()
