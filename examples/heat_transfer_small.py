from codar.cheetah import Campaign
from codar.cheetah import parameters as p

class HeatTransfer(Campaign):
    """Small example to run the heat_transfer application with stage_write,
    using no compression, zfp, or sz. All other options are fixed, so there
    are only three runs."""

    name = "heat-transfer-small"
    
    # This applications consists of two codes, with nicknames "heat" and "stage" and locations as specified
    codes = dict(heat="heat_transfer_adios2",
                 stage="stage_write/stage_write")
    
    # The application is designed to run on two machines. (These are magic strings known to Cheetah.)
    supported_machines = ['local', 'titan']
    
    # Inputs are copied to each "run directory" -- directory created by Cheetah for each run
    inputs = ["heat_transfer.xml"]

    project = "CSC242"
    queue = "debug"

    sweeps = [
        
     # Each SweepGroup specifies a set of runs to be performed on a specified number of nodes. 
     # Here we have 1 SweepGroup, which will run on 2 nodes.
     p.SweepGroup(nodes=2, # Number of nodes to run on
                  
      # Within a SweepGroup, each parameter_group specifies arguments for each of the parameters required for each code
      # Number of runs is the product of the number of options specified. Below, it is 2, as only one parameter has >1 arguments.
      # There are three types of parameters: system ("ParamRunner"), positional (ParamCmdLineArg), and a third (not used here)

      parameter_groups=
      [p.Sweep([
                   
      # First, the parameters for the STAGE program
          
        # ParamRunner passes an argument to launch_multi_swift
        p.ParamRunner("stage", "nprocs", [2]),   # nprocs: Number of processors (aka process) to use
          
        # ParamCmdLineArg passes a positional argument to the application
        # Arguments are: 
          # 1) Code name (e.g., "stage"), 
          # 2) Logical name for parameter, used in output; 
          # 3) positional argument number; 
          # 4) options
        p.ParamCmdLineArg("stage", "input", 1, ["heat.bp"]),
        p.ParamCmdLineArg("stage", "output", 2, ["staged.bp"]),
        p.ParamCmdLineArg("stage", "rmethod", 3, ["FLEXPATH"]),
        p.ParamCmdLineArg("stage", "ropt", 4, [""]),
        p.ParamCmdLineArg("stage", "wmethod", 5, ["MPI"]),
        p.ParamCmdLineArg("stage", "wopt", 6, [""]),
        p.ParamCmdLineArg("stage", "variables", 7, ["T,dT"]),
        p.ParamCmdLineArg("stage", "transform", 8,
                          ["none", "zfp:accuracy=.001", "sz:accuracy=.001"]),
        p.ParamCmdLineArg("stage", "decomp", 9, [2]),

      # Second, the parameters for the HEAT program

        p.ParamRunner("heat", "nprocs", [12]),
        p.ParamCmdLineArg("heat", "output", 1, ["heat"]),
        p.ParamCmdLineArg("heat", "xprocs", 2, [4]),
        p.ParamCmdLineArg("heat", "yprocs", 3, [3]),
        p.ParamCmdLineArg("heat", "xsize", 4, [40]),
        p.ParamCmdLineArg("heat", "ysize", 5, [50]),
        p.ParamCmdLineArg("heat", "steps", 6, [6]),
        p.ParamCmdLineArg("heat", "iterations", 7, [5]),
        ]),
      ]),
    ]
