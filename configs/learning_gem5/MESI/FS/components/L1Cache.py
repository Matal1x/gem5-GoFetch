import math

from m5.defines import buildEnv
from m5.util import fatal, panic

from m5.objects import *

class L1Cache(L1Cache_Controller):

    _version = 0

    @classmethod
    def versionCount(cls):
        cls._version += 1  # Use count for this particular type
        return cls._version - 1

    def __init__(self, board, ruby_system, core, 
        l1i_size: str,
        l1i_assoc: str,
        l1d_size: str,
        l1d_assoc: str,):
        """CPUs are needed to grab the clock domain and system is needed for
        the cache block size.
        """
        super(L1Cache, self).__init__()

        self.version = self.versionCount()

        self.L1Icache = RubyCache(size = l1i_size,
                                assoc = l1i_assoc,
                                start_index_bit=board.get_cache_line_size(),
                                is_icache = True)
        self.L1Dcache = RubyCache(size = l1d_size,
                            assoc = l1d_assoc,
                            start_index_bit=board.get_cache_line_size(),
                            is_icache = False)

        self.l2_select_num_bits=0
        self.clk_domain = board.get_clock_domain()
        self.send_evictions = core.requires_send_evicts()
        self.ruby_system = ruby_system
        self.connectQueues(ruby_system)

        self.prefetcher = RubyPrefetcher()
        self.enable_prefetch = True


    def connectQueues(self, ruby_system):
        """Connect all of the queues for this controller."""
        # Connect the L1 controllers and the network
        self.mandatoryQueue = MessageBuffer()
        self.requestFromL1Cache = MessageBuffer()
        self.requestFromL1Cache.out_port = ruby_system.network.in_port
        self.responseFromL1Cache = MessageBuffer()
        self.responseFromL1Cache.out_port = ruby_system.network.in_port
        self.unblockFromL1Cache = MessageBuffer()
        self.unblockFromL1Cache.out_port = ruby_system.network.in_port

        self.optionalQueue = MessageBuffer()

        self.requestToL1Cache = MessageBuffer()
        self.requestToL1Cache.in_port = ruby_system.network.out_port
        self.responseToL1Cache = MessageBuffer()
        self.responseToL1Cache.in_port = ruby_system.network.out_port