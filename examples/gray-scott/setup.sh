export PATH=$PATH:/Users/swithana/programs/openmpi/bin

OPEN_MPI_LIB=/Users/swithana/programs/openmpi/lib
export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:$OPEN_MPI_LIB

ADIOS_HOME=/Users/swithana/programs/adios2
export LD_LIBRARY_PATH=$ADIOS_HOME/lib:$LD_LIBRARY_PATH

export PYTHONPATH=$PYTHONPATH:/Users/swithana/programs/adios2/lib/python3.7/site-packages
export PATH=$PATH:$ADIOS_HOME/bin
