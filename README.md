# CODAR Cheetah - The CODAR Experiment Harness

## Overview

The CODAR Experiment Harness is designed to run Exascale science applications
using different parameters and components to determine the best combination
for deployment on different supercomputers.

To use Cheetah, the user first writes a "campaign" specification file. It
currently has four subcommands:

1. `create-campaign` - takes the campaign specification and generate a set of
  scripts to execute the application many times with each of the parameter
  sets, and organize the results of each run in separate subdirectories. Once
  generated, the `run-all.sh` script in the output directory can be used
  to run the campaign.
2. `status` - get status information about a campaign directory generated by
  the `create-campaign` command
3. `generate-report` - Generate a report of results from a completed campaign
4. `help` - get information about available commands

To get detailed help about options for each subcommand, execute the subcommand
with the `-h` option, e.g. `cheetah.py create-campaign -h`.

## Requirements

Cheetah requires a modern Linux install with Python 3.4 or greater and
numpy. Some cheetah functionality is designed to inter-operate with the
Savanna software stack, including ADIOS, Dataspaces, SOSFlow, and TAU, but
simple campaigns can be run without further dependencies.
See the [savanna documentation](https://github.com/CODARcode/savanna)
for more information and install instructions.

## Installation from github (for developers)

For development or to run the latest version of cheetah (or a feature
branch), you can clone the git repository and install in develop mode,
so any changes to the repository directory will be reflected immediately
in the python environment without re-installing a new version.

```
git clone https://github.com/CODARcode/cheetah.git
cd cheetah
# Recommended: create a venv or virtualenv
python3 -m venv venv-cheetah
source venv-cheetah/bin/activate
pip install --editable .
```

Note that any usage of cheetah will require using the python executable
within this virtualenv (via the activate script, manually setting PATH,
or using the absolute path the python exe). When running on super
computing centers, the virtualenv should be on a shared filesystem that
is also accessible by compute nodes. All campaigns generated by cheetah
will use the same python executable to run the workflow.py script on
compute nodes, unless this is overridden by setting `python_path` in the
campaign spec.

## Running the test suite

Running the tests requires having `nose` installed within the cheetah
virtualenv. Continuing from the github installation example above:
```
cd /path/to/cheetah
source venv-cheetah/bin/activate
pip install nose
```
Some of the tests use real CODAR example applications - to avoid having
to clone and build them for basic testing, you can have the test suite
generate a fake directory hierarchy for you:
```
export CODAR_APPDIR=fake
```
For more thorough testing, where you can submit the generated campaigns,
download and build the examples in a common directory:
```
export CODAR_APPIDR=/path/to/codar/apps
mkdir -p "$CODAR_APPDIR"
cd "$CODAR_APPDIR"
git clone https://github.com/CODARcode/Example-pi
git clone https://github.com/CODARcode/Example-Heat_Transfer
git clone https://github.com/CODARcode/Example-EXAALT
# Build each app according to it's instructions, including versions
# with and without tau for Heat_Transfer.
```
To run the test suite (from the top level cheetah directory):
```
tests/run-all.sh
```

## Tutorial for Running Heat Transfer example with Cheetah

1. Install Savanna and build the Heat Transfer example (see [savanna
   instructions](https://github.com/CODARcode/savanna/blob/master/README.md)).
   This tutorial will assume spack was used for the
   installation, and uses bash for environment setup examples.

2. Download the Cheetah v0.5.1 release from github and unpack the release
   [tarball](https://github.com/CODARcode/cheetah/archive/v0.5.1.tar.gz).

3. Install Cheetah to a venv or virtualenv:

```
cd /path/to/cheetah-0.5.1
python3 -m venv venv-cheetah
source venv-cheetah/bin/activate
pip install .
```

4. Set up the environment for cheetah (this can be added to your ~/.bashrc
   file for convenience, after the spack environment is loaded):

```
source <(spack module loads --dependencies adios)
```

5. Make a directory for storing campaigns, for example:

```
mkdir -p ~/codar/campaigns
```

6. Generate a campaign from the example, which will run Heat\_Transfer
   with stage\_write three times, once with no compression, once with
   zfp, and once with sz:

```
path2savanna = `spack find -p savanna | grep savanna | awk '{ print $2 }'`
cd /path/to/cheetah
./cheetah.py create-campaign -e examples/heat_transfer_small.py \
 -a $path2savanna/Heat_Transfer \
 -m local -o ~/codar/campaigns/heat
```

7. Run the campaign:

```
cd ~/codar/campaigns/heat/$USER
./run-all.sh
```

For run output, see `GROUP_NAME/run-NNN`. To debug submit failures, look at
`GROUP_NAME/codar.cheetah.submit-output.txt`. To view progress of the run,
start with the status command with no options, then use the options to drill
down and get more details on specific groups and runs. For example:

```
# show progress of each group in the campaign
cheetah.py status ~/codar/campaigns/heat

# get a summary of runs within a group
cheetah.py status ~/codar/campaigns/heat -g GROUP\_NAME -s

# show status of each run within a group
cheetah.py status ~/codar/campaigns/heat -g GROUP\_NAME -n

# show stderr and stdout for a specific run within a group
cheetah.py status ~/codar/campaigns/heat -g GROUP\_NAME -r RUN\_NAME -o
```

## Campaign Directory

Within the output directory, cheetah creates a subdirectory based on your
username. Within the user directory, there is a subdirectory for each group
in the specification. The `status` subcommand should be used as the first
method for investigating the progress of a campaign, but it can also be
useful to understand the structure and examine files directly.
Group directories contain the following files:

- submit.sh: script that submits the group to the scheduler (or runs in
  the background for local machine). The campaign `run-all.sh` script simply
  calls this script in every group subdirectory.
- status.sh: script that prints information about the status of a group that
  has been submitted. Output depends on the scheduler.
- cancel.sh: script to cancel the job, after submit has been called.
- codar.cheetah.jobid.txt: after the group is submitted, this will contain
  the job id (or PID for local machine), with the format SCHEDULER:ID, where
  SCHEDULER is one of PBS, COBALT, SLURM, or PID.
- codar.cheetah.walltime.txt: when the job is finished, this will contain a
  single line with the total walltime for the group in seconds.
- codar.FOBrun.log: log file for the workflow script (also called the FOB
  runner). First place to look for debugging. Exists only after the group is
  running.
- codar.workflow.status.json: File describing the state of each run within the
  group. See `status_summary.py` in the project root for an example script that
  generates a summary from this file. Exists only after the group is running.
- fobs.json: list of application runs within the group. Each line is a JSON
  document. Useful for verifying that cheetah has generated the correct
  commands for each code.

The group directory also contains subdirectories of the format `run-NNN` for
each application run in the group. The run directory contains the following
files:

- codar.cheetah.fob.json: The FOB, or functional object bundle, describing
  what commands are executed as part of this run. Identical the corresponding
  line in the group fobs.json. This may be useful for certain types of
  post processing scripts, but the run-params file described next is usually
  more useful.
- codar.cheetah.run-params.json: abstract description of all parameters in this
  run. Format is a dictionary of dictionaries, where top level keys are the
  code names, and each sub-dict describes the parameters for that code. Useful
  for post processing scripts.
- codar.cheetah.run-params.txt: list of commands that were run. Does not do
  quoting and does not include non command line parameters, but can be useful
  for quick manual verification.

For each code, the run directory will also contain the following files and
directories, with "CODE" used as a placeholder for the actual code name:

- codar.workflow.return.CODE: contains a single line with the return value of
  the code, once it is complete. If the code was never run successful, this
  file won't exist.
- codar.workflow.stdout.CODE: standard out for the code. Exists after the code
  is started.
- codar.workflow.stderr.CODE: standard error for the code.
- codar.workflow.walltime.CODE: walltime of the code in seconds, available
  if the code can be run and after it completes.
- codar.cheetah.tau-CODE: directory of tau output for the code. Will be empty
  if the code is not tau enabled.
- tau.conf: Tau configuration file. Ignored unless the application is tau
  enabled. A campaign can specify a file with the `tau_config` variable,
  otherwise a default file will be used.

Each code within the run will be executed with the working dir set to the run
directory, unless the `component_subdirs` option is set to True for the group.
In that case, the working dir  for each code will be a subdirectory of the run
directory with name equal to the code name.

## SOSFlow Support (beta)

Cheetah can automatically configure sosflow daemons to run with an application.
See [heat transfer example sosflow](examples/heat_transfer_sosflow.py). Note
that sosflow is enabled per code and per group - both must be set for a code
in a run within a group to use sosflow.

Output files from sosflow will be stored in the run directories (see
description below). Typically this will be `sosd.0000N.db` files.

## Campaign Specification

The campaign is specified as a python class that extends
`codar.cheetah.Campaign`. To define your own campaign, it is recommended to
start with the
[heat transfer example](examples/heat_transfer_simple.py).

Note that this is an early release and the campaign definition is not
stable yet. Here is a quick overview of the current structure and
supported parameter types. For a complete list, see the examples and the
[campaign class definition](codar/cheetah/model.py).

- name - a descriptive name for the campaign
- codes - a list of pairs describing the codes that make up the application.
  When running the application, codes will be executed in this order.
  The first value in the pair is the code name. The second value is a
  dictionary describing properties of the code. The 'exe' key is required,
  is assumed to be relative to the app directory specified on the cheetah
  command line if it's not an absolute path. The optional `sleep\_after` key
  can be used to delay execution of the next code. The `sosflow` boolean
  option is used to enable SOSFlow tracking for the code, for groups with
  `sosflow` set.
- supported\_machines - list of machines that the campaign is designed
  to run on. Currently only 'local' and 'titan' are supported.
- inputs - list of files relative to the application root directory to
  copy to the working directory for each application run. If the file is
  an adios config file, ParamAdiosXML can be used to modify it's
  contents as part of the parameter sweep.
- scheduler\_options - dictionary containing options for each machine. Top
  level keys are machine names, values are dictionaries containing scheduler
  options for that machine. `project` and `queue` are supported by all
  machines and schedulers, except for local machine (which has no scheduler).
  `cori` also supports `constraint` and `license`.
- sweeps - list of SweepGroup objects, defining instances of the
  application to run and what parameters to use.
- SweepGroup - each sweep group specifies the number of nodes (ignored
  for local runs), and a set of parameter groups. This represents a
  single submission to the scheduler, and each sweep group will be in a
  different subdirectory of the output directory.
- Sweep - a sweep is a specification of all the parameters that must be
  passed to each code in the application, together with metadata like
  the number of MPI processes to use for each code, and lists of all
  values that the parameters should take on for this part of the
  campaign. Within the sweep, a cross product of all the values will be
  taken to generate all the instances to run. For simple campaigns that
  need to do a full cross product of parameter values, only one
  SweepGroup containing one Sweep is needed.
- node\_layout - an option passed to the Sweep that determines the
  way to allocate nodes and MPI processes to codes. The default is to allocate
  an entire node to each code and use the maximum number of cores available.
  Alternate configuration is specified in a dictionary, with
  keys giving a machine name that the layout is designed for, and values
  indicating the layout as a list of dictionaries. Each dictionary
  represents a single node, the keys inside are code names, and the
  values are the number of processes to use for each code. Node sharing
  is not yet supported, so each node dictionary must contain only one code
  entry, but the format is designed to support sharing. See also the
  [node layout example](examples/heat_transfer_node_layout.py).
- ParamX - all parameter types have at least three elements:
  - target - which code the parameter is for. The value must be one of
    the keys in the codes dictionary.
  - name - logical name for the parameter. This is used as a key in the JSON
    file that is generated to describe the parameter values used for a
    run in the output directory. For each target, there can be only one
    parameter with a given name.
  - values - the list of values the parameter should take on for the
    sweep
  Different parameter types will have other parameters as well.
- ParamRunner - currently used only for the special 'nprocs' parameter
  to specify how many processes to use for each code.
- ParamCmdLineArg - positional arguments to pass to the code executable.
  The third argument is the position, starting from 1. All positions
  from 1 to the max must be included.
- ParamCmdLineOption - the third argument is the full option name,
  including any dashes, e.g. '--iterations' or '-iterations' depending
  on the convention used by the code. Note that this is distinct from
  the name, but a good choice for name is the option with the dashes
  removed.

## Changelog

### v0.5.1

- Refactor to better support installation via pip and setuptools
- Campaigns will use the same python executable as the
  `cheetah.py create-campaign` command used to generate them, which
  should automatically take care of using the correct virtualenv in most
  cases. For any exceptions, the `python_path` variable can be set in
  the campaign spec.

### v0.5

- New subcommand structure (the initial command structure is now under
  the `create-campaign` subcommand).
- New `status` subcommand
- New  `generate-report` subcommand
- Multi-user campaign support
- Specify different node counts in Sweeps
- Add experiments to an existing campaign directory
- Option to override number of nodes
- Feature to parse and consolidate campaign performance information
- Have cheetah figure out min/max number of nodes
- Mark file as ADIOS XML file for an application
- Support for absolute paths for input files
- Support for TAU trace directory
- Support for input files with key-value parameters
- Get Example-Heat_Transfer + Tau working with Cheetah
- Support for running per-run setup script during campaign creation
- Support for sub-directories for FOB components
- Named group directories in campaign
- Ordered invocation of FOB components
- Insert delay between component invocations
- Derived params based on params for codes
- Option to kill run if any component fails
- Support for timeouts
- Support for named arguments
- Set custom TAU environment variable for each code
- Dataspaces integration
- Improved ADIOS parameter support
- Add `node\_layout` Sweep option for per-machine node configuration
- Working machine support: local, cori, theta, and titan
- Add umask campaign option
- Per code/component input files
- Improved workflow scheduling (more efficient use of available nodes
  within a sweep group)
- Add new parameter types `ParamKeyValue` (for ini, namelist, and other
  similar name=value formatted config files) and `ParamConfig` (fully
  generic string replacment, can be used with any format)
- Add hook in report generation to run user script
- Support symlinks for input files, useful to avoid copying large files
- (beta) SOSFlow integration
- (beta) Resume partially completed campaigns


See the v0.5 milestone on github for a complete list including bug fixes:
https://github.com/CODARcode/cheetah/milestone/1?closed=1

### v0.1

- Initial release
- Working machine support: local, titan
