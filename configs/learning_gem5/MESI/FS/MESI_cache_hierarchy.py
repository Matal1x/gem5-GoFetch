import math

from m5.defines import buildEnv
from m5.util import fatal, panic
from gem5.utils.requires import requires

from m5.objects import *
from components.L1Cache import L1Cache
from components.L2Cache import L2Cache
from components.Directory import Directory
from components.DMA import DMAController
from components.MyNetwork import MyNetwork

from gem5.components.cachehierarchies.ruby.abstract_ruby_cache_hierarchy import AbstractRubyCacheHierarchy
from gem5.components.boards.abstract_board import AbstractBoard
from gem5.coherence_protocol import CoherenceProtocol
from gem5.isas import ISA

class MESITwoLevelCacheHierarchy(
    AbstractRubyCacheHierarchy
):
    """A two level private L1 shared L2 MESI hierarchy.
    """
    def __init__(
        self,
        l1i_size: str,
        l1i_assoc: str,
        l1d_size: str,
        l1d_assoc: str,
        l2_size: str,
        l2_assoc: str,
    ):
        AbstractRubyCacheHierarchy.__init__(self=self)
        
        self._l1i_size = l1i_size
        self._l1i_assoc = l1i_assoc
        self._l1d_size = l1d_size
        self._l1d_assoc = l1d_assoc
        self._l2_size = l2_size
        self._l2_assoc = l2_assoc

    def incorporate_cache(self, board: AbstractBoard) -> None:

        requires(coherence_protocol_required=CoherenceProtocol.MESI_TWO_LEVEL)
        cache_line_size = board.get_cache_line_size()
        cpus = board.get_processor().get_cores()

        self.ruby_system = RubySystem()
        self.ruby_system.number_of_virtual_networks = 3
        self.ruby_system.network = MyNetwork(self.ruby_system)
        self.ruby_system.network.number_of_virtual_networks = 3

        self.ruby_system.memory_size_bits = int(math.log2(board.mem_ranges[0].size()))

        self._l1_controllers = []
        for i, core in enumerate(board.get_processor().get_cores()):
            L1cache = L1Cache(board, self.ruby_system, core, self._l1i_size, self._l1i_assoc, self._l1d_size, self._l1d_assoc)
            L1cache.sequencer = RubySequencer(
                version=i,
                icache=L1cache.L1Icache,
                dcache=L1cache.L1Dcache,
                clk_domain=L1cache.clk_domain,
                ruby_system=self.ruby_system
            )
            if board.has_io_bus():
                L1cache.sequencer.connectIOPorts(board.get_io_bus())

            L1cache.ruby_system = self.ruby_system

            core.connect_icache(L1cache.sequencer.in_ports)
            core.connect_dcache(L1cache.sequencer.in_ports)
            core.connect_walker_ports(L1cache.sequencer.in_ports,
                                        L1cache.sequencer.in_ports)
            
            # Connect the interrupt ports
            if board.get_processor().get_isa() == ISA.X86:
                int_req_port = L1cache.sequencer.interrupt_out_port
                int_resp_port = L1cache.sequencer.in_ports
                core.connect_interrupt(int_req_port, int_resp_port)
            else:
                core.connect_interrupt()

            self._l1_controllers.append(L1cache)

        self._l2_controllers =[
            L2Cache(board, self.ruby_system, self._l2_size, self._l2_assoc)
        ]

        self._directory_controllers = []
        for range, port in board.get_mem_ports():
            dir = Directory(
                self.ruby_system,
                range,
                port,
            )
            self._directory_controllers.append(dir)    

        self._dma_controllers = []
        if board.has_dma_ports():
            dma_ports = board.get_dma_ports()
            for i, port in enumerate(dma_ports):
                ctrl = DMAController(self.ruby_system)
                ctrl.dma_sequencer = DMASequencer(version=i, in_ports=port)
                ctrl.dma_sequencer.ruby_system = self.ruby_system

                self._dma_controllers.append(ctrl)

        self.ruby_system.num_of_sequencers = len(self._l1_controllers) + len(self._dma_controllers)

        self.ruby_system.l1_controllers = self._l1_controllers
        self.ruby_system.l2_controllers = self._l2_controllers
        self.ruby_system.directory_controllers = self._directory_controllers
        if len(self._dma_controllers) != 0:
            self.ruby_system.dma_controllers = self._dma_controllers
        
        self.ruby_system.network.connectControllers(
            self._l1_controllers
            + self._l2_controllers
            + self._directory_controllers
            + self._dma_controllers
        )
        self.ruby_system.network.setup_buffers()
        self.ruby_system.sys_port_proxy = RubyPortProxy()
        board.connect_system_port(self.ruby_system.sys_port_proxy.in_ports)