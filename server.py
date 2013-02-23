# -*- coding: utf-8 -*-

import subprocess
import sys
from twisted.protocols.basic import LineReceiver
from twisted.conch.telnet import TelnetProtocol
from twisted.internet.protocol import Factory
from twisted.internet import reactor


logins = {
    'client1': 'pass1',
    'client2': 'pass2',
    'client3': 'pass3',
}


class TelnetToCli(LineReceiver, TelnetProtocol):

    def __init__(self, factory):
        self.factory = factory


    def connectionMade(self):
        self.transport.write('Username: ')
        self.state = 'USERNAME'


    def connectionLost(self, reason):
        self.transport.write('Bye!')
        pass


    def lineReceived(self, line):
        if 'exit' == line:
            self.state = 'EXIT'

        getattr(self, 'telnet_' + self.state)(line)


    def authenticate(self):
        assert self.factory.credentials[self.username] == self.password, "Authentication failed"


    def telnet_USERNAME(self, line):
        self.username = line
        self.transport.write('Password: ')
        self.state = 'PASSWORD'


    def telnet_PASSWORD(self, line):
        self.password = line
        try:
            self.authenticate()
        except KeyError:
            self.transport.write("This login does not exists! \n")
            self.transport.write('Username: ')
            self.state = 'USERNAME'
        except AssertionError:
            self.transport.write("This password is not correct! \n")
            self.transport.write('Password: ')
            self.state = 'PASSWORD'
        else:
            self.transport.write('Welcome! type "exit" to close connection. \n')
            self.transport.write('%s@telnetshell#: ' % self.username)
            self.state = 'AUTHENTICATED'


    def telnet_AUTHENTICATED(self, command):
        proc = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE)
        stdout_value = proc.communicate()[0]
        stdout_lines = stdout_value.split("\n")
        for line in stdout_lines:
            self.transport.write("> %s \n" % line)

        self.transport.write('%s@telnetshell#: ' % self.username)


    def telnet_EXIT(self, line):
        self.transport.loseConnection()


class TelnetToCliFactory(Factory):

    def __init__(self, credentials):
        self.credentials = credentials

    def buildProtocol(self, addr):
        return TelnetToCli(self)


if __name__ == "__main__":
    try:
        port = int(sys.argv[0])
    except:
        port = 4321
    reactor.listenTCP(port, TelnetToCliFactory(logins))
    reactor.run()

