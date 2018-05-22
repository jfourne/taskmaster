import time
import socket
import configurationClass as conf

class Client:

    host = str()
    port = int()
    history = list()
    conf_file = conf.ConfigurationFile()

    def __init__(self, sock=None):

        if sock == None:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        else:
            self.sock = sock

    def clientConnexion(self, host='127.0.0.1', port=12800):

        self.host = host
        self.port = port

        try:
            self.sock.connect((host, port))
            return 0
        except:
            print("Error: Can't connect to taskmaster daemon")
            return 1

    def sendMessage(self, message):

        try:
            message = bytes(message, 'UTF-8')
            self.sock.send(message)
            return 0
        except:
            print("\nError: Can't delivered message to taskmasterd")
            return 1

    def receiveMessage(self, buff=1024):
        self.sock.settimeout(0.05)
        try:
            message = self.sock.recv(buff)
            return message.decode()
        except socket.timeout:
            return ''
        except:
            print("Error: can't receive message from server")

    def closeConnection(self):

        self.sock.close()
        print("Connection close. Bye bye 3:)")

    def historyFileWrite(self, history):

        history_path = self.conf_file.parsed_file['taskmasterctl'].get('history_file', './history.txt')
        try:
            with open(history_path, 'w+') as history_file:
                for command in history:
                    history_file.write(command + '\n')
        except:
            print("Error: Can't open history file")
            return []
        history_file.close()

    def historyFileLoad(self):

        history_path = self.conf_file.parsed_file['taskmasterctl'].get('history_file', './history.txt')
        try:
            with open(history_path, 'r') as history_file:
                for current_line in history_file.readlines():
                    self.history.append(current_line.rstrip())
        except:
            return []
        history_file.close()
        return self.history

    def parse(self, line):

        if not line:
            return 2
        line = line.split()
        for arg in line:
            arg.strip()
        cmd = line[0]
        if cmd != 'start' and cmd != 'restart' and cmd != 'stop' and cmd != 'status' and cmd != 'reload' and cmd != 'close' and cmd != 'help' and cmd != 'shutdown':
            return 1
        if cmd == 'help':
            return 3
        return (' '.join(line))
