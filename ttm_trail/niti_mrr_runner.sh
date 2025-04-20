#!/bin/bash
# filepath: /home/rimuru/workspace/ttm_trail/niti_mrr_runner.sh

# Set base directories
WORKSPACE_DIR="/home/rimuru/workspace"
TTM_DIR="${WORKSPACE_DIR}/ttm_trail"
LOG_DIR="${TTM_DIR}/logs"
OUTPUT_DIR="${TTM_DIR}/output"
VISUAL_DIR="${TTM_DIR}/visualization"

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
mkdir -p ${OUTPUT_DIR}
mkdir -p ${LOG_DIR}
mkdir -p ${VISUAL_DIR}

# Define input and log files
NITI_INPUT="${TTM_DIR}/niti_mrr.lammps"
NITI_LOG="${LOG_DIR}/niti_edm_simulation.log"
RESTART_FILE="${OUTPUT_DIR}/niti_edm.restart"

echo "============================================================"
echo "Starting NiTi EDM Simulation: $(date)"
echo "============================================================"

# Check if input file exists
if [ ! -f "$NITI_INPUT" ]; then
    echo "ERROR: Input file $NITI_INPUT not found!"
    exit 1
fi

# Check if potential file exists
if [ ! -f "${TTM_DIR}/Ni-Ti.eam.fs" ]; then
    echo "ERROR: Potential file ${TTM_DIR}/Ni-Ti.eam.fs not found!"
    exit 1
fi

# Run LAMMPS with maximum GPU acceleration
echo "Running LAMMPS NiTi EDM Simulation with $GPU_COUNT GPUs..."
mpirun -n ${GPU_COUNT} lmp -k on g ${GPU_COUNT} -sf kk -pk kokkos cuda/aware on neigh full comm device binsize 2.8 \
    -in "$NITI_INPUT" > "$NITI_LOG" 2>&1

# Check if LAMMPS ran successfully
if [ $? -eq 0 ]; then
    echo "NiTi EDM simulation completed successfully."

    # Copy trajectory files to visualization directory for better organization
    if ls ${TTM_DIR}/dump.nitinol.*.lammpstrj > /dev/null 2>&1; then
        cp ${TTM_DIR}/dump.nitinol.*.lammpstrj ${VISUAL_DIR}/
        echo "Trajectory files copied to ${VISUAL_DIR}/"
    fi

    if ls ${TTM_DIR}/discharge.*.lammpstrj > /dev/null 2>&1; then
        cp ${TTM_DIR}/discharge.*.lammpstrj ${VISUAL_DIR}/
        echo "Discharge phase trajectories copied to ${VISUAL_DIR}/"
    fi

    if ls ${TTM_DIR}/melt_track.*.lammpstrj > /dev/null 2>&1; then
        cp ${TTM_DIR}/melt_track.*.lammpstrj ${VISUAL_DIR}/
        echo "Melt tracking trajectories copied to ${VISUAL_DIR}/"
    fi

    if [ -f "${TTM_DIR}/final_state.lammpstrj" ]; then
        cp ${TTM_DIR}/final_state.lammpstrj ${VISUAL_DIR}/
        echo "Final state file copied to ${VISUAL_DIR}/"
    fi
else
    echo "ERROR: NiTi EDM simulation failed! Check log file: $NITI_LOG"
    exit 1
fi

echo "NiTi EDM simulation ended at: $(date)"

# Generate summary report
echo "Generating simulation summary..."
cat > "${TTM_DIR}/niti_edm_summary.txt" << EOF
LAMMPS NiTi EDM Simulation Summary
=================================
Generated on $(date)

System Configuration:
- GPUs used: ${GPU_COUNT}
- LAMMPS executable: $(which lmp)
- MPI version: $(mpirun --version | head -n 1)
- Host system: $(hostname)
- System info: $(lsb_release -ds 2>/dev/null || cat /etc/os-release 2>/dev/null | grep PRETTY_NAME | sed 's/PRETTY_NAME=//' | tr -d '"')

Simulation Status:
--------------
EOF

if [ -f "$NITI_LOG" ]; then
    if grep -q "ERROR\|exited\|failed\|Segmentation fault" "$NITI_LOG"; then
        echo "Status: FAILED" >> "${TTM_DIR}/niti_edm_summary.txt"
    else
        echo "Status: COMPLETED" >> "${TTM_DIR}/niti_edm_summary.txt"

        # Extract runtime information
        RUNTIME=$(grep "Total wall time" "$NITI_LOG" | tail -n 1)
        if [ ! -z "$RUNTIME" ]; then
            echo "Runtime: $RUNTIME" >> "${TTM_DIR}/niti_edm_summary.txt"
        fi

        # Extract max temperature reached (specific to this simulation)
        MAX_TEMP=$(grep "Max temperature reached:" "$NITI_LOG" | tail -n 1)
        if [ ! -z "$MAX_TEMP" ]; then
            echo "$MAX_TEMP" >> "${TTM_DIR}/niti_edm_summary.txt"
        fi

        # Extract crater dimensions if available
        CRATER_INFO=$(grep -A 3 "Crater dimensions:" "$NITI_LOG" | tail -n 4)
        if [ ! -z "$CRATER_INFO" ]; then
            echo -e "\nCrater Analysis:" >> "${TTM_DIR}/niti_edm_summary.txt"
            echo "$CRATER_INFO" >> "${TTM_DIR}/niti_edm_summary.txt"
        fi
    fi
fi

echo "Simulation summary generated at: ${TTM_DIR}/niti_edm_summary.txt"

# Generate visualization helper script
cat > "${VISUAL_DIR}/view_results.sh" << EOF
#!/bin/bash
# Helper script to visualize results with OVITO

# Check if OVITO is installed
if command -v ovito &> /dev/null; then
    echo "Opening trajectory in OVITO..."
    ovito "${VISUAL_DIR}/final_state.lammpstrj"
else
    echo "OVITO not found. You can visualize the results by downloading OVITO from https://www.ovito.org/"
    echo "Available trajectory files:"
    ls -lh ${VISUAL_DIR}/*.lammpstrj
fi
EOF

chmod +x "${VISUAL_DIR}/view_results.sh"

echo "Visualization helper script created at: ${VISUAL_DIR}/view_results.sh"
echo "Run this script to open the results in OVITO (if installed)"

# Try to open results visualization if running in a GUI environment
if [ -f "${VISUAL_DIR}/final_state.lammpstrj" ] && [ ! -z "$DISPLAY" ]; then
    if command -v ovito &> /dev/null; then
        echo "Opening results in OVITO..."
        ovito "${VISUAL_DIR}/final_state.lammpstrj" &
    elif command -v $BROWSER &> /dev/null; then
        echo "Opening documentation in browser..."
        "$BROWSER" "https://www.ovito.org/manual/introduction/usage.html#loading-external-simulation-files" &
    fi
fi

echo "To run this script again: chmod +x $(basename $0) && ./$(basename $0)"
