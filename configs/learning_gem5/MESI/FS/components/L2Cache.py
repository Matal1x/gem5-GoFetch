import math

from m5.defines import buildEnv
from m5.util import fatal, panic

from m5.objects import *

class L2Cache(L2Cache_Controller):

    _version = 0

    @classmethod
    def versionCount(cls):
        cls._version += 1 # Use count for this particular type
        return cls._version - 1

    def __init__(self, board, ruby_system, 
        l2_size: str,
        l2_assoc: str,):
        super(L2Cache, self).__init__()
        self.version = self.versionCount()
        
        
        self.L2cache = RubyCache(size = l2_size,
                                assoc = l2_assoc,
                                start_index_bit=board.get_cache_line_size()) # We assume that here is only one L2 cache

        self.transitions_per_cycle = '4'
        self.ruby_system = ruby_system
        self.connectQueues(ruby_system)

    def connectQueues(self, ruby_system):
        """Connect all of the queues for this controller."""
        # Connect the L2 controllers and the network
        self.DirRequestFromL2Cache = MessageBuffer()
        self.DirRequestFromL2Cache.out_port = ruby_system.network.in_port
        self.L1RequestFromL2Cache = MessageBuffer()
        self.L1RequestFromL2Cache.out_port = ruby_system.network.in_port
        self.responseFromL2Cache = MessageBuffer()
        self.responseFromL2Cache.out_port = ruby_system.network.in_port

        self.unblockToL2Cache = MessageBuffer()
        self.unblockToL2Cache.in_port = ruby_system.network.out_port
        self.L1RequestToL2Cache = MessageBuffer()
        self.L1RequestToL2Cache.in_port = ruby_system.network.out_port
        self.responseToL2Cache = MessageBuffer()
        self.responseToL2Cache.in_port = ruby_system.network.out_port