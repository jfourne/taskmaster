import time
import curses, signal, os
import client
import configurationClass as conf
from curses import textpad

class InitTermios:

    configuration = conf.ConfigurationFile()
    client_created = client.Client()
    prompt = configuration.parsed_file['taskmasterctl']['prompt'] + " > "
    cursor_x = 0
    cursor_y = 0
    window_x = 0
    window_y = 0
    command_x = 0
    command_y = 9
    output_x = 0
    output_y = 15
    stdscr = 0
    line = []
    cant_print = False
    history = []
    h = 0
    i = 0

    def __init__(self):
        if self.client_created.clientConnexion() == 1:
            return
        self.history = self.client_created.historyFileLoad()
        self.h = len(self.history)
        signal.signal(signal.SIGINT, self.catchSigInt)
        signal.signal(signal.SIGWINCH, self.catchSigWinch)
        curses.wrapper(self.initWindow)

    def catchSigInt(self, signal, frame):
        self.stdscr.erase()
        self.tryDisplay()

    ##
    # A REVOIR EN FONCTION DES RETOUR POSSIBLE
    ##
    def catchSigWinch(self, signal, frame):
        rows, columns = os.popen('stty size', 'r').read().split()
        # self.stdscr.resize(int(rows), int(columns))
        curses.resizeterm(int(rows), int(columns))
        (get_window_y, get_window_x) = self.stdscr.getmaxyx()
        self.window_x = get_window_x
        self.window_y = get_window_y
        self.stdscr.erase()
        self.tryDisplay()
        # (cursor_tuple_y, cursor_tuple_x) = self.stdscr.getyx()
        # print(str(self.window_x), str(self.window_y), str(columns), str(rows))

    def printInInput(self):
        len_max_command = self.window_x * (self.output_y - self.command_y) - len(self.prompt) - (self.output_y - self.command_y) - 1
        if (len(self.line) > len_max_command):
            self.stdscr.insnstr(self.cursor_y, self.cursor_x, "Can't display input", 0)
        elif len(self.line) > 0:
            for line_char in self.line:
                self.stdscr.insch(self.cursor_y, self.cursor_x, line_char)
                self.cursor_x += 1
                if self.cursor_x == self.window_x - 1:
                    self.cursor_x = 0
                    self.cursor_y += 1
                self.stdscr.move(self.cursor_y, self.cursor_x)
                self.i += 1

    def printInOutput(self, message):
        output_max_len = (self.window_x - 2) * (self.window_y - self.output_y - 2) - (self.window_y - self.output_y - 2)
        end_line = 0
        for letter in message:
            if letter == '\n':
                end_line += 1
        # end_line = message.count('\n')
        # end_line += 1
        if end_line == 0:
            end_line = 1
        #
        # A VOIR POUR LE X MAX
        #
        if (len(message) > output_max_len) or end_line > (self.window_y - self.output_y - 2):
            self.stdscr.insnstr(self.output_y + 1, 2, "Can't display output", 0)
        else:
            message_split = message.split('\n')
            put_y = self.output_y
            for splitted in message_split:
                put_x = 2
                for letter in splitted:
                    self.stdscr.insch(put_y + 1, put_x, letter)
                    put_x += 1
                    if put_x >= self.window_x - 2:
                        put_x = 2
                        put_y += 1
                        if put_y - self.output_y - 1 >= (self.window_y - self.output_y - 2):
                            self.stdscr.erase()
                            self.resetWindow()
                            self.stdscr.insnstr(self.output_y + 1, 2, "Can't display output", 0)
                put_y += 1
            self.createFrame()


    def displayHeader(self):
        header1 = "  _____         _    __  __           _"
        header2 = " |_   _|_ _ ___| | _|  \/  | __ _ ___| |_ ___ _ __"
        header3 = "   | |/ _` / __| |/ / |\/| |/ _` / __| __/ _ \ '__|"
        header4 = "   | | (_| \__ \   <| |  | | (_| \__ \ ||  __/ |"
        header5 = "   |_|\__,_|___/_|\_\_|  |_|\__,_|___/\__\___|_|"

        center_header_x = self.window_x - 51
        self.stdscr.insnstr(0, int(center_header_x / 2), header1, 0)
        self.stdscr.insnstr(1, int(center_header_x / 2), header2, 0)
        self.stdscr.insnstr(2, int(center_header_x / 2), header3, 0)
        self.stdscr.insnstr(3, int(center_header_x / 2), header4, 0)
        self.stdscr.insnstr(4, int(center_header_x / 2), header5, 0)
        connexion_data = "Connexion established with {} on port {}" .format(self.client_created.host, self.client_created.port)
        center_connexion_data_x = self.window_x - len(connexion_data)
        self.stdscr.insnstr(self.command_y - 2, int(center_connexion_data_x / 2), connexion_data, 0)

    def resetWindow(self):
        self.i = 0
        self.cursor_y = self.command_y
        self.cursor_x = self.command_x + len(self.prompt)
        self.displayHeader()
        self.createFrame()
        self.stdscr.insnstr(self.cursor_y, 0, self.prompt, 0)
        self.stdscr.move(self.cursor_y, self.cursor_x)
        self.printInInput()
        self.cant_print = False

    def tryDisplay(self):
        if self.window_x < 53 or self.window_y < 20:
            self.stdscr.erase()
            self.stdscr.insnstr(0, 0, "Can't display Taskmaster", 0)
            self.cant_print = True
        # (cursor_tuple_y, cursor_tuple_x) = self.stdscr.getyx()
        else:
            self.resetWindow()

    def input(self, stdscr, close_window):
        end_read = False
        # if self.cant_print == True:
        #     end_read = True
        while (end_read == False):
            response = self.client_created.receiveMessage()
            if response != '' and response != '\n' and response != None:
                self.printInOutput(response)
                self.cursor_y = self.command_y
                self.cursor_x = self.command_x + len(self.prompt)
                self.stdscr.move(self.cursor_y, self.cursor_x)
            key = stdscr.getch()
            if self.cant_print == False:
                len_max_command = self.window_x * (self.output_y - self.command_y) - len(self.prompt) - (self.output_y - self.command_y) - 1
                #Return
                if (key == 10):
                    end_read = True
                    stdscr.erase()
                    # self.cursor_y += 1
                    result = self.client_created.parse(''.join(self.line))
                    if len(self.line) > 0:
                        self.h = len(self.history)
                        if self.h == 0:
                            self.history.append(''.join(self.line))
                            self.h += 1
                        elif self.history[-1] != ''.join(self.line):
                            self.history.append(''.join(self.line))
                            self.h += 1
                    if result == 1:
                        self.printInOutput("Error: bad command")
                    elif result == 2:
                        continue
                    elif result == 3:
                        self.printInOutput("""COMMANDS: - start <program>
                - restart <program>
                - stop <program>
                - status <program>
                - reload
                - close""")
                    else:
                        self.client_created.sendMessage(result)
                    if (''.join(self.line) == "close"):
                        close_window = True
                    self.line = []
                #Ctrl-C / Check Twice
                # elif (key == -1):
                #     end_read = True
                #     self.line = []
                #     stdscr.erase()
                    # self.cursor_y += 1
                # #Ctrl-L / Clear
                # elif key == 12:
                #     stdscr.erase()
                #     self.cursor_y = self.command_y
                #     stdscr.move(self.cursor_y, self.cursor_x)
                #     end_read = True
                #Esc / Ctrl-D
                elif key == 27 or key == 4:
                    end_read = True
                    close_window = True
                    self.client_created.sendMessage('close')
                #Suppr
                elif key == 127 and self.i > 0:
                    self.cursor_x -= 1
                    if self.cursor_x < 0:
                        self.cursor_x = self.window_x - 2
                        self.cursor_y -= 1
                    stdscr.delch(self.cursor_y, self.cursor_x)
                    del self.line[self.i - 1]
                    self.i -= 1
                #Delete
                elif key == 330 and self.i < len(self.line):
                    stdscr.delch(self.cursor_y, self.cursor_x)
                    del self.line[self.i]
                #Home
                elif key == 262:
                    self.i = 0
                    self.cursor_x = self.command_x + len(self.prompt)
                    self.cursor_y = self.command_y
                    stdscr.move(self.command_y, self.cursor_x)
                #End
                elif key == 360:
                    self.i = len(self.line)
                    self.cursor_x = int((len(self.line) + len(self.prompt)) % self.window_x) + self.command_x + 1
                    self.cursor_y = int((len(self.line) + len(self.prompt)) / self.window_x) + self.command_y
                    stdscr.move(self.cursor_y, self.cursor_x)
                #Arrow_up
                elif key == 259 and self.h > 0:
                    self.h -= 1
                    self.line = []
                    for j in self.history[self.h]:
                        self.line.append(j)
                    self.stdscr.erase()
                    self.resetWindow()
                #Arrow_down
                elif key == 258 and self.h < len(self.history):
                    if self.h < len(self.history) - 1:
                        self.h += 1
                        self.line = []
                        for j in self.history[self.h]:
                            self.line.append(j)
                        self.stdscr.erase()
                        self.resetWindow()
                    else:
                        self.h += 1
                        self.line = []
                        self.stdscr.erase()
                        self.resetWindow()
                #Arrow_left
                elif key == 260 and self.cursor_x > len(self.prompt):
                    self.cursor_x -= 1
                    if self.cursor_x < 0:
                        self.cursor_x = self.window_x - 2
                        self.cursor_y -= 1
                    self.i -= 1
                    stdscr.move(self.cursor_y, self.cursor_x)
                #Arrow_right
                elif key == 261 and self.i < len(self.line):
                    self.cursor_x += 1
                    if self.cursor_x == self.window_x - 1:
                        self.cursor_x = 0
                        self.cursor_y += 1
                    self.i += 1
                    stdscr.move(self.cursor_y, self.cursor_x)
                #Printable
                elif key >= 32 and key < 127 and len(self.line) < len_max_command:
                    stdscr.insch(self.cursor_y, self.cursor_x, key)
                    self.cursor_x += 1
                    if self.cursor_x == self.window_x - 1:
                        self.cursor_x = 0
                        self.cursor_y += 1
                    stdscr.move(self.cursor_y, self.cursor_x)
                    self.line.insert(self.i, chr(key))
                    self.i += 1
        if (close_window == True):
            return True
        else:
            return False

    def windowManager(self, stdscr):
        close_window = False
        while (close_window == False):
            self.tryDisplay()
            close_window = self.input(stdscr, close_window)
            # if len(self.line) > 0:
            #     print("  ##### ", ''.join(self.line))
            if (close_window == True):
                self.client_created.closeConnection()
        if len(self.history) >= 100:
            self.history = self.history[60:]
        self.client_created.historyFileWrite(self.history)

    def initWindow(self, stdscr):
        # Clear screen
        stdscr.clear()
        self.stdscr = stdscr
        self.stdscr.nodelay(True)
        # (cursor_tuple_y, cursor_tuple_x) = stdscr.getyx()
        (self.window_y, self.window_x) = self.stdscr.getmaxyx()
        self.windowManager(stdscr)
        stdscr.refresh()

    def createFrame(self):
        textpad.rectangle(self.stdscr, self.output_y, 0, self.window_y - 1, self.window_x - 2)
