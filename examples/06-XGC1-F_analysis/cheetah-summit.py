from codar.cheetah import Campaign
from codar.cheetah import parameters as p
from codar.savanna.machines import SummitNode
from codar.cheetah.parameters import SymLink
import copy
from math import floor


class GrayScott(Campaign):
    # A name for the campaign
    name = "XGC1-f_analysis"

    # Input base directory
    XGC_INPUT_BASE_DIR = "/gpfs/alpine/scratch/swithana/csc143/xgc-f/exp-xgc-ftt-demo/xgc_work_cheetah/*"
    FTT_INPUT_BASE_DIR = "/gpfs/alpine/scratch/swithana/csc143/xgc-f/exp-xgc-ftt-demo/ftt_work_cheetah/*"
    XGC1_inputs = "/gpfs/alpine/scratch/swithana/csc143/xgc-f/exp-xgc-ftt-demo/setup2/XGC-1_inputs"

    # Define your workflow. Setup the applications that form the workflow.
    # exe may be an absolute path.
    # The adios xml file is automatically copied to the campaign directory.
    # 'runner_override' may be used to launch the code on a login/service node as a serial code
    #   without a runner such as aprun/srun/jsrun etc.
    codes = [("simulation", dict(exe="xgc-es")),
             ("f_analysis", dict(exe="xgc-f0", runner_override=False)), ]

    # List of machines on which this code can be run
    supported_machines = ['local', 'titan', 'theta', 'summit']

    # Kill an experiment right away if any workflow components fail (just the experiment, not the whole group)
    kill_on_partial_failure = True

    # Any setup that you may need to do in an exper
    run_dir_setup_script = None

    # A post-process script that is run for every experiment after the experiment completes
    run_post_process_script = None

    # Directory permissions for the campaign sub-directories
    umask = '027'

    # Options for the underlying scheduler on the target system. Specify the project ID and job queue here.
    scheduler_options = {'theta': {'project': 'CSC249ADCD01', 'queue': 'default'},
                         'summit': {'project': 'csc299'}}

    # A way to setup your environment before the experiment runs. Export environment variables such as LD_LIBRARY_PATH here.
    app_config_scripts = {'local': 'setup.sh', 'theta': 'env_setup.sh', 'summit': 'setup.sh'}

    # Setup the sweep parameters for a Sweep
    sweep1_parameters = [
        # ParamRunner 'nprocs' specifies the no. of ranks to be spawned
        p.ParamRunner('simulation', 'nprocs', [8 * 6]),

        # Create a ParamCmdLineArg parameter to specify a command line argument to run the application
        # p.ParamCmdLineArg   ('simulation', 'settings', 1, ["settings.json"]),
        #
        # # Edit key-value pairs in the json file
        # # Sweep over two values for the F key in the json file.
        # p.ParamConfig       ('simulation', 'feed_rate_U', 'settings.json', 'F', [0.01]),
        # p.ParamConfig       ('simulation', 'kill_rate_V', 'settings.json', 'k', [0.048]),
        # p.ParamConfig       ('simulation', 'domain_size', 'settings.json', 'L', [1024]),
        # p.ParamConfig       ('simulation', 'num_steps', 'settings.json', 'steps', [50]),
        # p.ParamConfig       ('simulation', 'plot_gap', 'settings.json', 'plotgap', [10]),
        #
        # # Setup an environment variable
        # p.ParamEnvVar       ('simulation', 'openmp', 'OMP_NUM_THREADS', [4]),

        # Change the engine for the 'SimulationOutput' IO object in the adios xml file to SST for coupling.
        # As both the applications use the same xml file, you need to do this just once.
        # p.ParamADIOS2XML('simulation', 'SimulationOutput', 'engine', [{'SST': {}}]),

        # Now setup options for the f_analysis application.
        # Sweep over four values for the nprocs
        p.ParamRunner('f_analysis', 'nprocs', [8]),
        # p.ParamCmdLineArg   ('f_analysis', 'infile', 1, ['gs.bp']),
        # p.ParamCmdLineArg   ('f_analysis', 'outfile', 2, ['pdf']),
    ]

    # Create the node-layout to run on summit
    # Place the simulation and the analysis codes on separate nodes
    # On Summit, create a 'node' object and manually map ranks to cpus and gpus using the convention
    # cpu[index] = code_name:rank_id
    # Given this node mapping and the 'nprocs' property, Cheetah will automatically spawn the correct no. 
    # of nodes. For example, for the simulation, we have 32 ranks on one node and 512 nprocs, so Cheetah
    # will create 16 nodes of type 'sim_node'
    sim_node = SummitNode()
    pdf_node = SummitNode()
    for i in range(32):
        sim_node.cpu[i] = "simulation:{}".format(i)
    for i in range(32):
        pdf_node.cpu[i] = "f_analysis:{}".format(i)
    separate_node_layout = [sim_node, pdf_node]

    # Create a Sweep object. This one does not define a node-layout, and thus, all cores of a compute node will be
    #   utilized and mapped to application ranks.
    sweep1 = p.Sweep(parameters=sweep1_parameters, node_layout={'summit': separate_node_layout})

    # Create another Sweep object and set its node-layout to spawn 16 simulation processes per node, and 
    #   4 processes of f_analysis per node. On Theta, different executables reside on separate nodes as node-sharing
    #   is not permitted on Theta.
    sweep2_parameters = copy.deepcopy(sweep1_parameters)

    # Now create a shared node layout where ranks from different codes are placed on the node
    # Lets place 32 ranks of the simulation and 8 ranks of f_analysis on the same node
    shared_node = SummitNode()
    for i in range(18):
        shared_node.cpu[i] = "simulation:{}".format(floor(i / 6))
        shared_node.cpu[i + 21] = "simulation:{}".format(floor((i + 18) / 6))
    for i in range(3):
        shared_node.cpu[i + 18] = "f_analysis:0"
        shared_node.cpu[i + 18 + 21] = "f_analysis:0"
    shared_node_layout = [shared_node]

    sweep2 = p.Sweep(parameters=sweep2_parameters, node_layout={'summit': shared_node_layout})

    # Create a SweepGroup and add the above Sweeps. Set batch job properties such as the no. of nodes, 
    sweepGroup1 = p.SweepGroup("summit-xgc-f1-1",  # A unique name for the SweepGroup
                               walltime=60,  # Total runtime for the SweepGroup
                               per_run_timeout=60,  # Timeout for each experiment
                               parameter_groups=[sweep2],  # Sweeps to include in this group
                               launch_mode='default',  # Launch mode: default, or MPMD if supported
                               nodes=8,  # No. of nodes for the batch job.
                               component_subdirs=True,
                               # <-- codes have their own separate workspace in the experiment directory
                               component_inputs={'simulation': [SymLink(XGC_INPUT_BASE_DIR), SymLink(XGC1_inputs)],
                                                 'f_analysis': [SymLink(FTT_INPUT_BASE_DIR), SymLink(XGC1_inputs)]},
                               # rc_dependency={'f_analysis':'simulation',}, # Specify dependencies between workflow components
                               run_repetitions=0,
                               # No. of times each experiment in the group must be repeated (Total no. of runs here will be 3)
                               )

    # Activate the SweepGroup
    sweeps = [sweepGroup1]
