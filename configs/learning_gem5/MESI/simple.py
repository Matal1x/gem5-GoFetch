# -*- coding: utf-8 -*-
# Adapted config script for MESI_2_CacheSystem

import os
import math
import m5
from m5.objects import *
import m5.util
m5.util.addToPath("../../")
from common.FileSystemConfig import config_filesystem


from myMESIconfig import MESI_2_CacheSystem  

# Create the system object
system = System()

# Set clock domain for the system and children
system.clk_domain = SrcClockDomain()
system.clk_domain.clock = "1GHz"
system.clk_domain.voltage_domain = VoltageDomain()

# Set system memory mode and ranges
system.mem_mode = "timing"
system.mem_ranges = [AddrRange('8GB')]


# Create CPUs
num_cpus = 2
system.cpu = [TimingSimpleCPU(cpu_id=i) for i in range(num_cpus)]

# Create a memory controller and connect to membus
system.mem_ctrl = MemCtrl()
system.mem_ctrl.dram = DDR4_2400_8x8()
system.mem_ctrl.dram.range = system.mem_ranges[0]

system.membus = SystemXBar()

# Interrupt controllers for each CPU
for cpu in system.cpu:
    cpu.createInterruptController()
    cpu.interrupts[0].pio = system.membus.mem_side_ports
    cpu.interrupts[0].int_requestor = system.membus.cpu_side_ports
    cpu.interrupts[0].int_responder = system.membus.mem_side_ports
# If you have DMA controllers, create and collect them here
dma_ctrls = []  # List of DMA controllers if any, else empty

# Create your MESI 2-level cache system
system.ruby = MESI_2_CacheSystem()
system.ruby.setup(system, system.cpu, [system.mem_ctrl], dma_ctrls)
system.ruby.memory_size_bits = int(math.log2(system.mem_ranges[0].size())) ## THIS PARAMETER IS IMPORTANT




# Setup workload binary path
thispath = os.path.dirname(os.path.realpath(__file__))
binary = os.path.join(
    thispath,
    "../../../",
    "tests/test-progs/threads/bin/x86/linux/threads",
)

# Create process and assign workload
process = Process()
process.cmd = [binary]
for cpu in system.cpu:
    cpu.workload = process
    cpu.createThreads()

system.workload = SEWorkload.init_compatible(binary)

# Setup pseudo file system for the workload
config_filesystem(system)

# Set up the root SimObject and instantiate
root = Root(full_system=False, system=system)
m5.instantiate()

print("Beginning simulation!")
exit_event = m5.simulate()
print(f"Exiting @ tick {m5.curTick()} because {exit_event.getCause()}")
