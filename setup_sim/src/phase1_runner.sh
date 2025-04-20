#!/bin/bash
# filepath: /home/rimuru/workspace/setup_sim/src/run_phase1.sh

# Set base directories
WORKSPACE_DIR="/home/rimuru/workspace"
SRC_DIR="${WORKSPACE_DIR}/setup_sim/src"
DATA_DIR="${WORKSPACE_DIR}/setup_sim/data"
LOG_DIR="${WORKSPACE_DIR}/setup_sim/logs"
SCRIPTS_DIR="${WORKSPACE_DIR}/setup_sim/scripts"

# Auto-detect available GPUs (dynamic configuration)
if command -v nvidia-smi &> /dev/null; then
    GPU_COUNT=$(nvidia-smi --list-gpus | wc -l)
    echo "Auto-detected ${GPU_COUNT} NVIDIA GPUs"
else
    echo "NVIDIA GPU detection failed. Checking for other methods..."
    if [ -d "/proc/driver/nvidia/gpus" ]; then
        GPU_COUNT=$(ls -1 /proc/driver/nvidia/gpus | wc -l)
        echo "Found ${GPU_COUNT} NVIDIA GPUs via /proc"
    else
        echo "No GPUs detected. Defaulting to CPU mode (1 process)"
        GPU_COUNT=1
    fi
fi

echo "Will use ${GPU_COUNT} GPU device(s) for maximum performance"

# Create necessary directories
mkdir -p ${DATA_DIR}/phase1
mkdir -p ${LOG_DIR}
mkdir -p ${WORKSPACE_DIR}/setup_sim/inputs
mkdir -p ${SCRIPTS_DIR}

# Define phase 1 input and log files
PHASE1_INPUT="${SRC_DIR}/phase1.lammps"
PHASE1_LOG="${LOG_DIR}/phase1.log"

echo "============================================================"
echo "Starting Phase 1 (Equilibration): $(date)"
echo "============================================================"

# Check if input file exists
if [ ! -f "$PHASE1_INPUT" ]; then
    echo "ERROR: Input file $PHASE1_INPUT not found!"
    exit 1
fi

# Run LAMMPS with maximum GPU acceleration using the precise format
echo "Running LAMMPS Phase 1 with $GPU_COUNT GPUs..."
mpirun -n ${GPU_COUNT} lmp -k on g ${GPU_COUNT} -sf kk -pk kokkos cuda/aware on neigh full comm device binsize 2.8 \
    -var x 8 -var y 4 -var z 8 \
    -in "$PHASE1_INPUT" > "$PHASE1_LOG" 2>&1

# Check if LAMMPS ran successfully
if [ $? -eq 0 ]; then
    echo "Phase 1 completed successfully."

    # Make restart file accessible for future use
    if [ -f "${DATA_DIR}/phase1/equil.restart" ]; then
        mkdir -p ${SCRIPTS_DIR}
        cp ${DATA_DIR}/phase1/equil.restart ${SCRIPTS_DIR}/
        echo "Restart file copied to ${SCRIPTS_DIR}/equil.restart"
    else
        echo "WARNING: Restart file not found at expected location."
    fi
else
    echo "ERROR: Phase 1 failed! Check log file: $PHASE1_LOG"
    exit 1
fi

echo "Phase 1 simulation ended at: $(date)"

# Generate summary report
echo "Generating phase 1 summary..."
cat > "${WORKSPACE_DIR}/setup_sim/phase1_summary.txt" << EOF
LAMMPS Phase 1 Summary
======================
Generated on $(date)

System Configuration:
- GPUs used: ${GPU_COUNT}
- LAMMPS executable: $(which lmp)
- MPI version: $(mpirun --version | head -n 1)
- Host system: $(hostname)
- System info: $(lsb_release -ds 2>/dev/null || cat /etc/os-release 2>/dev/null | grep PRETTY_NAME | sed 's/PRETTY_NAME=//' | tr -d '"')

Phase 1 Status:
--------------
EOF

if [ -f "$PHASE1_LOG" ]; then
    if grep -q "ERROR\|exited\|failed\|Segmentation fault" "$PHASE1_LOG"; then
        echo "Status: FAILED" >> "${WORKSPACE_DIR}/setup_sim/phase1_summary.txt"
    else
        echo "Status: COMPLETED" >> "${WORKSPACE_DIR}/setup_sim/phase1_summary.txt"

        # Extract runtime information
        RUNTIME=$(grep "Total wall time" "$PHASE1_LOG" | tail -n 1)
        if [ ! -z "$RUNTIME" ]; then
            echo "Runtime: $RUNTIME" >> "${WORKSPACE_DIR}/setup_sim/phase1_summary.txt"
        fi

        # Extract temperature and pressure
        TEMP=$(grep "Final Temperature:" "$PHASE1_LOG" | tail -n 1)
        PRESS=$(grep "Final Pressure:" "$PHASE1_LOG" | tail -n 1)
        PE=$(grep "Potential Energy:" "$PHASE1_LOG" | tail -n 1)
        DENS=$(grep "System Density:" "$PHASE1_LOG" | tail -n 1)

        if [ ! -z "$TEMP" ]; then
            echo "$TEMP" >> "${WORKSPACE_DIR}/setup_sim/phase1_summary.txt"
        fi

        if [ ! -z "$PRESS" ]; then
            echo "$PRESS" >> "${WORKSPACE_DIR}/setup_sim/phase1_summary.txt"
        fi

        if [ ! -z "$PE" ]; then
            echo "$PE" >> "${WORKSPACE_DIR}/setup_sim/phase1_summary.txt"
        fi

        if [ ! -z "$DENS" ]; then
            echo "$DENS" >> "${WORKSPACE_DIR}/setup_sim/phase1_summary.txt"
        fi
    fi
fi

echo "Phase 1 summary generated at: ${WORKSPACE_DIR}/setup_sim/phase1_summary.txt"

# Open the results in browser if any visualization exists
if [ -f "${DATA_DIR}/phase1/temp_profile.phase1.test.dat" ]; then
    echo "Phase 1 data files available at: ${DATA_DIR}/phase1/"
fi

echo "To run this script again: chmod +x $(basename $0) && ./$(basename $0)"
