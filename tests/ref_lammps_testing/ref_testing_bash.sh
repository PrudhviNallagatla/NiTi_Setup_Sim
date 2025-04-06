#!/bin/bash
# Run script for NiTi nanoparticle simulation
# Composition: Ni50.0Ti50.0
# Size: 1.25 nm
# Config: ../../../../config/simulation/yaml_configs/Ni50.0-Ti50.0/config_Ni50.0_Ti50.0_1.25nm.yaml

set -euf -o pipefail

# Path to this directory and simulation directory
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
SIM_DIR="$DIR"  # Use current directory for simulation
PYTHON_SCRIPT="/home/rimuru/workspace/src/core/sim_generator.py"

# Create data, trajectory, and log directories in current dir
mkdir -p $SIM_DIR/data
mkdir -p $SIM_DIR/trajectories
mkdir -p $SIM_DIR/logs

# Get number of available GPUs (more robust version)
GPU_COUNT=$(nvidia-smi --list-gpus | wc -l 2>/dev/null || echo "1")
# Use at least one GPU
GPU_COUNT=${GPU_COUNT:-1}

echo "====================================================================="
echo "Regenerating input file from YAML configuration"
echo "====================================================================="

# Regenerate the LAMMPS input file from the YAML config - uncomment if needed
# python3 $PYTHON_SCRIPT --update-input "/home/rimuru/workspace/config/simulation/yaml_configs/Ni50.0-Ti50.0/config_Ni50.0_Ti50.0_1.25nm.yaml" "$SIM_DIR/lmp_Ni50.0_Ti50.0_1.25nm_sim.lammps"

# if [ $? -ne 0 ]; then
#     echo "Error: Failed to regenerate input file from YAML config"
#     exit 1
# fi

echo "====================================================================="
echo "Running simulation in the current directory: $SIM_DIR"
echo "====================================================================="

# Copy the reference LAMMPS input if needed (uncomment if you want this)
# cp /home/rimuru/workspace/data/simulations/Ni50.0-Ti50.0/1.25nm/lmp_Ni50.0_Ti50.0_1.25nm_sim.lammps $SIM_DIR/

# Run LAMMPS with GPU acceleration
mpirun -n ${GPU_COUNT} lmp -k on g ${GPU_COUNT} \
    -sf kk \
    -pk kokkos cuda/aware on neigh full comm device binsize 2.8 \
    -var potential_dir /home/rimuru/workspace/config/simulation/potentials \
    -in /home/rimuru/workspace/tests/ref_lammps_testing/ref_script.lammps

echo "====================================================================="
echo "Simulation completed successfully!"
echo "Log files are available in $SIM_DIR/logs/"
echo "====================================================================="
