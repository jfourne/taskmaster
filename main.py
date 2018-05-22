import configurationClass as Conf
import client as Client
import init_termios

path = "./taskmasterd.conf"

Conf.ConfigurationFile(path)
my_client = Client.Client()
init_termios.InitTermios()
