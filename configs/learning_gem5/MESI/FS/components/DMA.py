import math

from m5.defines import buildEnv
from m5.util import fatal, panic

from m5.objects import *

class DMAController(DMA_Controller):

    _version = 0

    @classmethod
    def versionCount(cls):
        cls._version += 1 # Use count for this particular type
        return cls._version - 1

    def __init__(self, ruby_system):
        super(DMAController, self).__init__()
        self.version = self.versionCount()
        self.ruby_system = ruby_system
        self.connectQueues(ruby_system)

    def connectQueues(self, ruby_system):
        self.mandatoryQueue = MessageBuffer()
        self.responseFromDir = MessageBuffer(ordered=True)
        self.responseFromDir.in_port = ruby_system.network.out_port
        self.requestToDir = MessageBuffer()
        self.requestToDir.out_port = ruby_system.network.in_port