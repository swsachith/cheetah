"""
Configuration for machines supported by Codar.
"""
from codar.savanna import exc
import json


# Note: not all schedulers support all options, the purpose of this is
# just basic validation to catch mispelling or completely unsupported
# options. Some options have different names, we favor PBS naming when
# possible. For example, queue is mapped to partition on cori/slurm.
# TODO: deeper validation, probably bring back a scheduler model.
SCHEDULER_OPTIONS = set(["project", "queue", "constraint", "license"])


class MachineNode:
    def __init__(self, num_cpus, num_gpus):
        # self.id = id
        self.cpu = [None] * num_cpus
        self.gpu = [None] * num_gpus

    def validate_layout(self):
        raise NotImplemented

    def to_json(self):
        raise NotImplemented

class SummitNode(MachineNode):
    def __init__(self):
        MachineNode.__init__(self, 42, 6)

    def validate_layout(self):
        """Check that 1) the same rank of the same code is not repeated,
        2) a gpu is not mapped to multiple executables."""

        # Assert node config is not empty
        assert not all(core_map is None for core_map in self.cpu), \
            "core mapping in nodeconfig is all None"

        # core_map = [v for v in self.cpu if v is not None]
        # assert len(core_map) == len(set(core_map)), \
        #     "duplicate mapping found in nodeconfig"

        # Assert gpu mapping is a list and not a string
        for e in self.gpu:
            if e is not None:
                assert type(e) == list, "gpu mapping values must be a list " \
                                        "of processes"

        # gpu_map = [v for v in self.gpu if v is not None]
        # assert len(gpu_map) == len(set(gpu_map)), \
        #     "duplicated mapping found in node config"

        # Assert that a gpu is not mapped to different executables
        for l in self.gpu:
            if l is not None:
                gpu_code_map = [v.split(":")[0] for v in l]
                assert all(x == gpu_code_map[0] for x in gpu_code_map), \
                    "cannot map different executables to the same gpu"

        # assert that all PEs from 0 through max are on the node and that
        # the user has not forgotten any

    def to_json(self):
        self.__dict__['__info_type__'] = 'NodeConfig'
        return self.__dict__


class Machine(object):
    """Class to represent configuration of a specific Supercomputer or
    workstation, including the scheduler and runner used by the machine.
    This can be used to map an experiment to run on the machine without
    having to define machine specific parameter for every experiment
    separately."""

    def __init__(self, name, scheduler_name, runner_name, node_class,
                 processes_per_node=None, node_exclusive=False,
                 scheduler_options=None, dataspaces_servers_per_node=1):
        self.name = name
        self.scheduler_name = scheduler_name
        self.runner_name = runner_name
        self.node_class = node_class
        # TODO: should the workflow script have knowledge of different
        # machines, or just generic options configured by Cheetah?
        self.processes_per_node = processes_per_node
        self.node_exclusive = node_exclusive
        _check_known_scheduler_options(SCHEDULER_OPTIONS, scheduler_options)
        self.scheduler_options = scheduler_options or {}
        self.dataspaces_servers_per_node = dataspaces_servers_per_node

    def get_scheduler_options(self, options):
        """Validate supplied options and add default values where missing.
        Returns a new dictionary."""
        supported_set = set(self.scheduler_options.keys())
        _check_known_scheduler_options(supported_set, options)
        new_options = dict(self.scheduler_options)
        new_options.update(options)
        return new_options

    def get_nodes_reqd(self):
        pass


def _check_known_scheduler_options(supported_set, options):
    if options is None:
        return
    unknown = set(options.keys()) - supported_set
    if unknown:
        raise ValueError("Unsupported scheduler option(s): "
                         + ",".join(opt for opt in unknown))


# All machine names must be lowercase, to avoid conflicts with class
# definitions etc. This allows the module to act as a sort of enum
# container with all the machines.

# NOTE: set process per node to avoid errors with sosflow calculations
local = Machine('local', "local", "mpiexec", MachineNode, processes_per_node=1)

titan = Machine('titan', "pbs", "aprun", MachineNode,
                processes_per_node=16, node_exclusive=True,
                scheduler_options=dict(project="", queue="debug"),
                dataspaces_servers_per_node=4)

# TODO: remove node exclusive restriction, which can be avoided on cori
# using correct sbatch and srun options. As a start just get feature
# parity with titan.
cori = Machine('cori', "slurm", "srun", MachineNode,
               processes_per_node=32, node_exclusive=True,
               dataspaces_servers_per_node=4,
               scheduler_options=dict(project="",
                                      queue="debug",
                                      constraint="haswell",
                                      license="SCRATCH,project"))


theta = Machine('theta', "cobalt", "aprun", MachineNode,
                processes_per_node=64, node_exclusive=True,
                dataspaces_servers_per_node=8,
                scheduler_options=dict(project="",
                                       queue="debug-flat-quad"))


summit = Machine('summit', "ibm_lsf", "jsrun", SummitNode,
                 processes_per_node=42, node_exclusive=True,
                 scheduler_options=dict(project=""))


def get_by_name(name):
    assert name == name.lower()
    try:
        return globals()[name]
    except KeyError:
        raise exc.MachineNotFound(name)
