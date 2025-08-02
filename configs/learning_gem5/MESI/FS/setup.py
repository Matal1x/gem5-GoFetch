import argparse

from gem5.coherence_protocol import CoherenceProtocol
from gem5.components.boards.x86_board import X86Board

from gem5.components.memory.single_channel import SingleChannelDDR3_1600
from gem5.components.processors.cpu_types import CPUTypes
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

parser = argparse.ArgumentParser()
parser.add_argument(
    "--binary",
    type=str,
    required=True,
    help="The binary to run in the simulation.",
)
args = parser.parse_args()


cache_hierarchy = MESITwoLevelCacheHierarchy(
    l1d_size="32KiB",
    l1d_assoc=8,
    l1i_size="32KiB",
    l1i_assoc=8,
    l2_size="256KiB",
    l2_assoc=16,
)

memory = SingleChannelDDR3_1600(size="2GiB")

processor = SimpleSwitchableProcessor(
    starting_core_type=CPUTypes.ATOMIC,
    switch_core_type=CPUTypes.TIMING,
    isa=ISA.X86,
    num_cores=2,
)

board = X86Board(
    clk_freq="3GHz",
    processor=processor,
    memory=memory,
    cache_hierarchy=cache_hierarchy,
)

command = (
    "m5 exit;"
    + "echo 'This is running on Timing CPU cores.';"
    + "m5 readfile > /tmp/guest_binary;"
    + "echo 'Done reading file.';"
    + "chmod +x /tmp/guest_binary;"
    + "echo 'Granted execution permission.';"
    + "bash"
)

board.set_kernel_disk_workload(
    kernel=obtain_resource("x86-linux-kernel-5.4.49"),
    disk_image=obtain_resource("x86-ubuntu-18.04-img"),
    readfile_contents=command
)
# build/X86_MESI_Two_Level/gem5.opt     configs/learning_gem5/MESI_Two_Level/FS/setup.py     --binary="/import/lab/users/aslaoui/gem5-Okapi/tests/test-progs/threads/bin/x86/linux/test0"

# FIX: Use a more explicit and correct generator function for the handler.
def handle_cpu_switch():
    # This function will be called when the first 'm5 exit' is hit.
    print("--- CPU switch exit event detected. Switching CPU... ---")
    processor.switch()
    # This 'yield False' is the crucial part. It tells the simulator
    # to continue running and not to exit.
    yield False

simulator = Simulator(
    board=board,
    on_exit_event={
        # Assign the generator function to handle the EXIT event.
        ExitEvent.EXIT: handle_cpu_switch()
    },
)
simulator.run()