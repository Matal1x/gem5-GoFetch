import argparse
import os

from gem5.coherence_protocol import CoherenceProtocol
from gem5.components.boards.x86_board import X86Board

from gem5.components.memory.single_channel import SingleChannelDDR3_1600
from gem5.components.processors.cpu_types import CPUTypes
from gem5.components.processors.simple_processor import SimpleProcessor
from gem5.components.processors.simple_switchable_processor import (
    SimpleSwitchableProcessor,
)
from gem5.isas import ISA
from gem5.resources.resource import obtain_resource
from gem5.simulate.exit_event import ExitEvent
from gem5.simulate.simulator import Simulator
from gem5.utils.requires import requires

from MESI_cache_hierarchy import MESITwoLevelCacheHierarchy

requires(
    isa_required=ISA.X86,
    coherence_protocol_required=CoherenceProtocol.MESI_TWO_LEVEL,
    kvm_required=False,
)

cache_hierarchy = MESITwoLevelCacheHierarchy(
    l1d_size="32KiB",
    l1d_assoc=8,
    l1i_size="32KiB",
    l1i_assoc=8,
    l2_size="256KiB",
    l2_assoc=16,
)

memory = SingleChannelDDR3_1600(size="2GiB")

processor = SimpleProcessor(
    cpu_type=CPUTypes.TIMING,
    isa=ISA.X86,
    num_cores=1,
)

board = X86Board(
    clk_freq="3GHz",
    processor=processor,
    memory=memory,
    cache_hierarchy=cache_hierarchy,
)

# The command is now simpler. It just runs until the OS is booted
# and then exits once.
command = (
    "echo 'OS Booted on Timing CPU. Ready for checkpoint.';"
    + "m5 exit;"
)

board.set_kernel_disk_workload(
    kernel=obtain_resource("x86-linux-kernel-5.4.49"),
    disk_image=obtain_resource("x86-ubuntu-18.04-img"),
    readfile_contents=command,
)

# We no longer need a special on_exit_event handler because we are not switching CPUs.
simulator = Simulator(board=board)

print("--- Starting simulation in TIMING mode to create checkpoint... ---")
print("--- This will be VERY slow. ---")
simulator.run()

# After the simulation finishes, we save the checkpoint.
checkpoint_dir = "checkpoints"
print(f"--- Simulation finished. Saving checkpoint to '{checkpoint_dir}' ---")

if not os.path.exists(checkpoint_dir):
    os.makedirs(checkpoint_dir)

simulator.save_checkpoint(checkpoint_dir)
print("--- Checkpoint saved successfully. ---")
