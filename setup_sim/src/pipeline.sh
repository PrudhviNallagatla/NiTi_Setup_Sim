#!/bin/bash
# filepath: /home/rimuru/workspace/setup_sim/src/pipeline.sh

# Set base directories
WORKSPACE_DIR="/home/rimuru/workspace"
SRC_DIR="${WORKSPACE_DIR}/setup_sim/src"
DATA_DIR="${WORKSPACE_DIR}/formation_sim/data"
LOG_DIR="${WORKSPACE_DIR}/formation_sim/logs"
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
mkdir -p ${DATA_DIR}/{phase1,phase2,phase3,phase4}
mkdir -p ${LOG_DIR}
mkdir -p ${WORKSPACE_DIR}/formation_sim/inputs
mkdir -p ${SCRIPTS_DIR}

# Function to run a LAMMPS phase with error handling and maximum GPU acceleration
run_lammps_phase() {
    local phase=$1
    local input_file="${SRC_DIR}/phase${phase}.lammps"
    local log_file="${LOG_DIR}/phase${phase}.log"

    echo "============================================================"
    echo "Starting Phase ${phase}: $(date)"
    echo "============================================================"

    # Check if input file exists
    if [ ! -f "$input_file" ]; then
        echo "ERROR: Input file $input_file not found!"
        return 1
    fi

    # Run LAMMPS with maximum GPU acceleration using the precise format
    # Use all detected GPUs with optimized parameters
    mpirun -n ${GPU_COUNT} lmp -k on g ${GPU_COUNT} -sf kk -pk kokkos cuda/aware on neigh full comm device binsize 2.8 \
        -var x 8 -var y 4 -var z 8 \
        -in "$input_file" > "$log_file" 2>&1

    # Check if LAMMPS ran successfully
    if [ $? -eq 0 ]; then
        echo "Phase ${phase} completed successfully."
        return 0
    else
        echo "ERROR: Phase ${phase} failed! Check log file: $log_file"
        return 1
    fi
}

# Clean any stale files from previous runs
echo "Cleaning up any stale restart/data files..."
rm -f ${SCRIPTS_DIR}/equil.restart
rm -f ${SCRIPTS_DIR}/ablation_final.restart
rm -f ${SCRIPTS_DIR}/nanoparticle_final.data

# Main execution
echo "Starting full simulation at: $(date)"
echo "Using ${GPU_COUNT} GPUs for maximum acceleration"

# Phase 1: Initial Setup & Equilibration
if run_lammps_phase 1; then
    # Make sure restart file is accessible for phase 2
    mkdir -p ${SCRIPTS_DIR}
    cp ${DATA_DIR}/phase1/equil.restart ${SCRIPTS_DIR}/

    # Phase 2: Spark Ablation
    if run_lammps_phase 2; then
        # Make sure restart file is accessible for phase 3
        cp ${DATA_DIR}/phase2/ablation_final.restart ${SCRIPTS_DIR}/

        # Phase 3: Nanoparticle Formation
        if run_lammps_phase 3; then
            # Make sure data file is accessible for phase 4
            cp ${DATA_DIR}/phase3/nanoparticle_final.data ${SCRIPTS_DIR}/

            # Phase 4: Analysis Methods
            if run_lammps_phase 4; then
                echo "Full simulation completed successfully!"

                # Run Python post-processing if present
                if [ -f "${DATA_DIR}/phase4/post_process.py" ]; then
                    echo "Running post-processing analysis..."
                    cd ${DATA_DIR}/phase4
                    python post_process.py
                    cd - > /dev/null
                fi

                # Open the visualization in browser if it exists
                if [ -f "${DATA_DIR}/phase4/size_distribution.png" ]; then
                    echo "Opening visualization in browser..."
                    "$BROWSER" "file://${DATA_DIR}/phase4/size_distribution.png"
                fi
            else
                echo "Simulation stopped at Phase 4 (Analysis)"
            fi
        else
            echo "Simulation stopped at Phase 3 (Nanoparticle Formation)"
        fi
    else
        echo "Simulation stopped at Phase 2 (Spark Ablation)"
    fi
else
    echo "Simulation stopped at Phase 1 (Equilibration)"
fi

echo "Simulation ended at: $(date)"

# Generate summary report
echo "Generating simulation summary..."
cat > "${WORKSPACE_DIR}/formation_sim/simulation_summary.txt" << EOF
LAMMPS Simulation Summary
=========================
Generated on $(date)

System Configuration:
- GPUs used: ${GPU_COUNT}
- LAMMPS executable: $(which lmp)
- MPI version: $(mpirun --version | head -n 1)
- Host system: $(hostname)
- System info: $(lsb_release -ds 2>/dev/null || cat /etc/os-release 2>/dev/null | grep PRETTY_NAME | sed 's/PRETTY_NAME=//' | tr -d '"')

Phase Status:
------------
EOF

for i in {1..4}; do
    if [ -f "${LOG_DIR}/phase${i}.log" ]; then
        if grep -q "ERROR\|exited\|failed\|Segmentation fault" "${LOG_DIR}/phase${i}.log"; then
            echo "Phase ${i}: FAILED" >> "${WORKSPACE_DIR}/formation_sim/simulation_summary.txt"
        else
            echo "Phase ${i}: COMPLETED" >> "${WORKSPACE_DIR}/formation_sim/simulation_summary.txt"

            # Extract runtime information if available
            RUNTIME=$(grep "Total wall time" "${LOG_DIR}/phase${i}.log" | tail -n 1)
            if [ ! -z "$RUNTIME" ]; then
                echo "  - $RUNTIME" >> "${WORKSPACE_DIR}/formation_sim/simulation_summary.txt"
            fi

            # Extract additional statistics based on phase
            case $i in
                1)
                    # Extract temperature and pressure for phase 1
                    TEMP=$(grep "Final Temperature:" "${LOG_DIR}/phase${i}.log" | tail -n 1)
                    PRESS=$(grep "Final Pressure:" "${LOG_DIR}/phase${i}.log" | tail -n 1)
                    if [ ! -z "$TEMP" ] && [ ! -z "$PRESS" ]; then
                        echo "  - $TEMP" >> "${WORKSPACE_DIR}/formation_sim/simulation_summary.txt"
                        echo "  - $PRESS" >> "${WORKSPACE_DIR}/formation_sim/simulation_summary.txt"
                    fi
                    ;;
                2)
                    # Extract ablation stats for phase 2
                    EJECTED=$(grep "Number of ejected atoms:" "${LOG_DIR}/phase${i}.log" | tail -n 1)
                    if [ ! -z "$EJECTED" ]; then
                        echo "  - $EJECTED" >> "${WORKSPACE_DIR}/formation_sim/simulation_summary.txt"
                    fi
                    ;;
                3)
                    # Extract nanoparticle stats for phase 3
                    CLUSTERS=$(grep "Final number of nanoparticle clusters:" "${LOG_DIR}/phase${i}.log" | tail -n 1)
                    if [ ! -z "$CLUSTERS" ]; then
                        echo "  - $CLUSTERS" >> "${WORKSPACE_DIR}/formation_sim/simulation_summary.txt"
                    fi
                    ;;
                4)
                    # Extract analysis stats for phase 4
                    PARTICLES=$(grep "Number of identified nanoparticles:" "${LOG_DIR}/phase${i}.log" | tail -n 1)
                    SIZE=$(grep "Average nanoparticle size:" "${LOG_DIR}/phase${i}.log" | tail -n 1)
                    if [ ! -z "$PARTICLES" ] && [ ! -z "$SIZE" ]; then
                        echo "  - $PARTICLES" >> "${WORKSPACE_DIR}/formation_sim/simulation_summary.txt"
                        echo "  - $SIZE" >> "${WORKSPACE_DIR}/formation_sim/simulation_summary.txt"
                    fi
                    ;;
            esac
        fi
    else
        echo "Phase ${i}: NOT RUN" >> "${WORKSPACE_DIR}/formation_sim/simulation_summary.txt"
    fi
done

echo "Summary generated at: ${WORKSPACE_DIR}/formation_sim/simulation_summary.txt"
echo "To run the simulation: chmod +x $(basename $0) && ./$(basename $0)"
