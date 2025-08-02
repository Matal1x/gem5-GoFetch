import math

from m5.defines import buildEnv
from m5.util import fatal, panic

from m5.objects import *

# This config is based on the msi example from the learning-gem5 ruby tutorial
#   and borrows code from other configs present in src and configs folders
class MESI_2_CacheSystem(RubySystem):
    def __init__(self):
        if buildEnv["PROTOCOL"] != "MESI_Two_Level":
            fatal("This system assumes MESI_Two_Level")

        super(MESI_2_CacheSystem, self).__init__()

    def setup(self, system, cpus, mem_ctrls, dma_ports):
        """Set up the Ruby cache subsystem. Note: This can't be done in the
        constructor because many of these items require a pointer to the
        ruby system (self). This causes infinite recursion in initialize()
        if we do this in the __init__.
        """
        # Ruby's global network.
        self.network = MyNetwork(self)

        # MESI_Two_Level uses 3 virtual networks.
        self.number_of_virtual_networks = 3
        self.network.number_of_virtual_networks = 3

        self.controllers = [L1Cache(system, self, cpu) for cpu in cpus] + \
                        [L2Cache(system, self)] + \
                        [DirController(self, system.mem_ranges, mem_ctrls)] + \
                        [DMAController(self) for dma in dma_ports]

        print("Hello I am here before the sequencers")
    
        # L2 and Dir don't need a sequencer as they don't have a mandatoryQueue
        self.sequencers = [
            RubySequencer(
                version=i,
                icache=self.controllers[i].L1Icache,
                dcache=self.controllers[i].L1Dcache,
                clk_domain=self.controllers[i].clk_domain,
                ruby_system=self
            ) for i in range(len(cpus))
            ] + [
                DMASequencer(
                    version=i, 
                    ruby_system=self,
                    in_ports=dma_port
                ) for i, dma_port in enumerate(dma_ports)
            ]

        print("AFTER the sequencers")


        for i, c in enumerate(self.controllers[0 : len(self.sequencers)]):
            c.sequencer = self.sequencers[i]
        
        print("OUGABOUGA")

        
        dma_start = len(cpus) + 2  # L1s + L2 + Dir
        for i, ctrl in enumerate(self.controllers[dma_start:]):
            ctrl.dma_sequencer = self.sequencers[len(cpus) + i]
        
        print("PUTTANA")


        self.num_of_sequencers = len(self.sequencers)

        # Create the network and connect the controllers.
        # NOTE: This is quite different if using Garnet!
        self.network.connectControllers(self.controllers)
        self.network.setup_buffers()

        # Set up a proxy port for the system_port. Used for load binaries and
        # other functional-only things.
        self.sys_port_proxy = RubyPortProxy()
        system.system_port = self.sys_port_proxy.in_ports
        self.sys_port_proxy.ruby_system = self
        # Connect the cpu's cache, interrupt, and TLB ports to Ruby
        for i,cpu in enumerate(cpus):
            cpu.icache_port = self.sequencers[i].in_ports
            cpu.dcache_port = self.sequencers[i].in_ports
            


class L1Cache(L1Cache_Controller):

    _version = 0

    @classmethod
    def versionCount(cls):
        cls._version += 1  # Use count for this particular type
        return cls._version - 1

    def __init__(self, system, ruby_system, cpu):
        """CPUs are needed to grab the clock domain and system is needed for
        the cache block size.
        """
        super(L1Cache, self).__init__()

        self.version = self.versionCount()

        self.L1Icache = RubyCache(size = "32kB",
                                assoc = 8,
                                start_index_bit=self.getBlockSizeBits(system),
                                is_icache = True)
        self.L1Dcache = RubyCache(size = "32kB",
                            assoc = 8,
                            start_index_bit=self.getBlockSizeBits(system),
                            is_icache = False)

        self.l2_select_num_bits=0
        self.clk_domain = cpu.clk_domain
        self.send_evictions = True
        self.ruby_system = ruby_system
        self.connectQueues(ruby_system)

        self.prefetcher = RubyPrefetcher(block_size=64)
        self.enable_prefetch = True


    def getBlockSizeBits(self, system):
        bits = int(math.log(system.cache_line_size, 2))
        if 2**bits != system.cache_line_size.value:
            panic("AAAAAAAAAAAAAAAAAAAAAAAAA Cache line size not a power of 2!")
        return bits


    def sendEvicts(self, cpu):
        """True if the CPU model or ISA requires sending evictions from caches
        to the CPU. Two scenarios warrant forwarding evictions to the CPU:
        1. The O3 model must keep the LSQ coherent with the caches
        2. The x86 mwait instruction is built on top of coherence
        3. The local exclusive monitor in ARM systems

        As this is an X86 simulation we return True.
        """
        return True


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



class L2Cache(L2Cache_Controller):

    _version = 0

    @classmethod
    def versionCount(cls):
        cls._version += 1 # Use count for this particular type
        return cls._version - 1

    def __init__(self, system, ruby_system):
        super(L2Cache, self).__init__()
        self.version = self.versionCount()
        
        
        self.L2cache = RubyCache(size = '64kB',
                                assoc = 8,
                                start_index_bit=self.getBlockSizeBits(system)) # We assume that here is only one L2 cache

        self.transitions_per_cycle = '4'
        self.ruby_system = ruby_system
        self.connectQueues(ruby_system)


    def getBlockSizeBits(self, system):
        bits = int(math.log(system.cache_line_size, 2))
        if 2**bits != system.cache_line_size.value:
            panic("YO YO Cache line size not a power of 2!")
        return bits


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



class DirController(Directory_Controller):

    _version = 0

    @classmethod
    def versionCount(cls):
        cls._version += 1  # Use count for this particular type
        return cls._version - 1

    def __init__(self, ruby_system, ranges, mem_ctrls):
        """ranges are the memory ranges assigned to this controller."""
        if len(mem_ctrls) > 1:
            panic("This cache system can only be connected to one mem ctrl")
        super(DirController, self).__init__()
        self.version = self.versionCount()
        self.addr_ranges = ranges
        self.ruby_system = ruby_system
        self.directory = RubyDirectoryMemory()
        self.directory.block_size = 64
        # Connect this directory to the memory side.
        self.memory = mem_ctrls[0].port
        self.connectQueues(ruby_system)

    def connectQueues(self, ruby_system):
        self.requestToDir = MessageBuffer()
        self.requestToDir.in_port = ruby_system.network.out_port
        self.responseToDir = MessageBuffer()
        self.responseToDir.in_port = ruby_system.network.out_port
        self.responseFromDir = MessageBuffer()
        self.responseFromDir.out_port = ruby_system.network.in_port
        self.requestToMemory = MessageBuffer()
        self.responseFromMemory = MessageBuffer()


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



class MyNetwork(SimpleNetwork):
    """A simple point-to-point network. This doesn't not use garnet."""

    def __init__(self, ruby_system):
        super(MyNetwork, self).__init__()
        self.netifs = []
        self.ruby_system = ruby_system

    def connectControllers(self, controllers):
        """Connect all of the controllers to routers and connec the routers
        together in a point-to-point network.
        """
        # Create one router/switch per controller in the system
        self.routers = [Switch(router_id=i) for i in range(len(controllers))]

        # Make a link from each controller to the router. The link goes
        # externally to the network.
        self.ext_links = [
            SimpleExtLink(link_id=i, ext_node=c, int_node=self.routers[i])
            for i, c in enumerate(controllers)
        ]

        # Make an "internal" link (internal to the network) between every pair
        # of routers.
        link_count = 0
        int_links = []
        for ri in self.routers:
            for rj in self.routers:
                if ri == rj:
                    continue  # Don't connect a router to itself!
                link_count += 1
                int_links.append(
                    SimpleIntLink(link_id=link_count, src_node=ri, dst_node=rj)
                )
        self.int_links = int_links