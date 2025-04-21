#!/bin/bash
# filepath: /workspace/ttm_trail/niti_mrr_runner.sh

# Set base directories
WORKSPACE_DIR="/workspace"
TTM_DIR="${WORKSPACE_DIR}/ttm_trail"
LOG_DIR="${TTM_DIR}/logs"
OUTPUT_DIR="${TTM_DIR}/output"

# Auto-detect available GPUs
if command -v nvidia-smi &> /dev/null; then
    GPU_COUNT=$(nvidia-smi --list-gpus | wc -l)
    echo "Auto-detected ${GPU_COUNT} NVIDIA GPUs"
else
    echo "No GPUs detected. Defaulting to CPU mode"
    GPU_COUNT=1
fi

# Detect CPU cores
CPU_CORES=$(nproc)
echo "Detected ${CPU_CORES} CPU cores"

# Create necessary directories
mkdir -p ${OUTPUT_DIR} ${LOG_DIR}

# Define input and log files
NITI_INPUT="${TTM_DIR}/niti_mrr.lammps"
NITI_LOG="${LOG_DIR}/niti_edm_simulation.log"

echo "Starting NiTi EDM Simulation: $(date)"

# GPU run (commented out but preserved)
# echo "Running LAMMPS with GPU acceleration..."
# mpirun -n ${GPU_COUNT} lmp -k on g ${GPU_COUNT} -sf kk -pk kokkos cuda/aware on neigh full comm device binsize 2.8 \
#     -in "$NITI_INPUT" > "$NITI_LOG" 2>&1

# CPU-only run - fixed Kokkos configuration
echo "Running LAMMPS in standard CPU mode using ${CPU_CORES} cores..."
# Remove Kokkos flags: -k on g 0 t ${CPU_CORES} -sf kk -pk kokkos openmp
mpirun -n ${CPU_CORES} /opt/deepmd-kit/install/bin/lmp \
    -in "$NITI_INPUT" > "$NITI_LOG" 2>&1

# Check if LAMMPS ran successfully
if [ $? -eq 0 ]; then
    echo "NiTi EDM simulation completed successfully."

    # Copy final state if available
    if [ -f "${TTM_DIR}/final_state.lammpstrj" ]; then
        cp ${TTM_DIR}/final_state.lammpstrj ${OUTPUT_DIR}/
    fi
else
    echo "ERROR: NiTi EDM simulation failed! Check log file: $NITI_LOG"
    exit 1
fi

echo "NiTi EDM simulation ended at: $(date)"
