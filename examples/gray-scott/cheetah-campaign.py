from codar.cheetah import Campaign
from codar.cheetah import parameters as p
from codar.cheetah.parameters import SymLink
import copy


class GrayScott(Campaign):
    name = "gray_scott"

    codes = [("simulation", dict(exe="gray-scott",
                                 adios_xml_file='adios2.xml')),
             ("pdf_calc", dict(exe="pdf_calc", adios_xml_file='adios2.xml')),
             ]

    # A list of machines that this campaign must be supported on
    # supported_machines = ['local', 'titan', 'theta']
    supported_machines = ['local']

    # Option to kill an experiment (just one experiment, not the full sweep or campaign) if one of the codes fails
    kill_on_partial_failure = True

    # Some pre-processing in the experiment directory
    # This is performed when the campaign directory is created (before the campaign is launched)
    run_dir_setup_script = None

    # A post-processing script to be run in the experiment directory after the experiment completes
    # For example, removing some large files after the experiment is done
    run_post_process_script = None

    # umask applied to your directory in the campaign so that colleagues can view files
    umask = '027'

    # Scheduler information: job queue, account-id etc. Leave it to None if running on a local machine
    # scheduler_options = {'titan': {'project':'CSC249ADCD01', 'queue': 'batch'}}

    # Setup your environment. Loading modules, setting the LD_LIBRARY_PATH etc.
    # Ensure this script is executable
    # app_config_scripts = {'local': 'setup.sh', 'titan': 'env_setup.sh'}
    app_config_scripts = {'local': 'setup.sh'}

    sim_input = ["settings.json"]

    sweep1_parameters = [
        p.ParamRunner('simulation', 'nprocs', [2, ]),
        p.ParamCmdLineArg('simulation', 'settings', 1, ["settings.json"]),
        p.ParamConfig('simulation', 'feed_rate_U', 'settings.json', 'F', [0.01, ]),
        p.ParamConfig('simulation', 'kill_rate_V', 'settings.json', 'k', [0.048]),
        p.ParamEnvVar('simulation', 'openmp', 'OMP_NUM_THREADS', [4, 8]),

        p.ParamRunner('pdf_calc', 'nprocs', [1]),
        p.ParamCmdLineArg('pdf_calc', 'infile', 1, ['gs.bp']),
        p.ParamCmdLineArg('pdf_calc', 'outfile', 2, ['pdf']),
    ]

    sweep1 = p.Sweep(node_layout={'titan': [{'simulation': 16}, ]},
                     parameters=sweep1_parameters)
    sweepGroup1 = p.SweepGroup("sg-1", walltime=1000, per_run_timeout=300,
                               component_inputs={"simulation": sim_input},
                               parameter_groups=[sweep1], launch_mode='default',
                               nodes=6, max_procs=6,
                               rc_dependency={'pdf_calc': 'simulation', }
                               )
    sweeps = [sweepGroup1]
