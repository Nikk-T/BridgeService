import logging
from mdp_protocol import *

log = logging.getLogger("protocol")

class SLSProtocol:

    def __init__(self, transport):

        self.transport = transport

    def rgb(self, ch, r, g, b):

        self.transport.write(cmd_rgb_level(ch, r, g, b))

    def blackout(self):

        self.transport.write(cmd_broadcast_off())

    def suspend(self):

        self.transport.write(cmd_subcmd(0, SUBCMD_SUSPEND))

    def resume(self):

        self.transport.write(cmd_subcmd(0, SUBCMD_RESUME))

    def keepalive(self):

        self.transport.write(cmd_nop(0))