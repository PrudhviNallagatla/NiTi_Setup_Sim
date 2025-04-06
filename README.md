# Micro-EDM Nitinol Nanoparticle Formation Simulation

## Project Summary

- **Purpose**: Simulate the formation of nitinol nanoparticles during micro-EDM processes
- **Simulation Approach**: 4-phase LAMMPS simulation modeling the complete particle formation process
- **Target Hardware**: GPU-accelerated computing (GTX 1650 for testing, more powerful for production)
- **Initial Validation**: 1nm size nanoparticles on GTX 1650
- **Final Target**: Parameter sweep of sizes 1-20nm, various compositions and conditions
- **Environment**: VS Code Dev Container with LAMMPS GPU support

## Physical Process Being Simulated

This simulation models the complete micro-EDM (Electrical Discharge Machining) process for creating nitinol nanoparticles:

1. **Phase 1 - Vaporization**: When the electrical arc hits the nitinol workpiece, intense localized heating causes material to vaporize
2. **Phase 2 - Plasma Cooling**: The vaporized nitinol particles cool in the plasma channel created by the discharge
3. **Phase 3 - Condensation**: The cooled particles condense in the surrounding dielectric fluid (water)
4. **Phase 4 - Coagulation**: The condensed particles aggregate and form stable nitinol nanoparticles

Each phase is modeled separately using specialized LAMMPS scripts with appropriate physical parameters and boundary conditions.

## Container Setup

- **Base Image**: nvcr.io/hpc/lammps:patch_15Jun2023
- **GPU Access**: Full passthrough via "--gpus=all"
- **Python Environment**: Pre-installed scientific packages (numpy, scipy, ase, etc.)
- **LAMMPS Build**: Includes KOKKOS package for GPU acceleration
- **Development**: Full VS Code integration with extensions for Python/C++

## Simulation Phases Explained

### Phase 1: Vaporization
- Simulates rapid heating when the electrical discharge hits the nitinol workpiece
- Uses NVT ensemble with extremely high temperature ramp (>10,000K)
- Monitors atomic dispersion, phase changes, and thermal properties
- Output: Vaporized atomic positions and velocities

### Phase 2: Plasma Cooling
- Models cooling of vaporized particles in the plasma channel
- Implements a controlled temperature reduction with specific cooling rates
- Accounts for plasma channel conditions (pressure, temperature gradients)
- Output: Partially cooled atomic clusters

### Phase 3: Condensation
- Simulates interaction with dielectric fluid (water molecules)
- Implements water molecules as explicit particles with appropriate force fields
- Tracks formation of initial small clusters as particles condense
- Output: Condensed nanoclusters with water interfaces

### Phase 4: Coagulation
- Models final aggregation of smaller clusters into stable nanoparticles
- Implements long-time dynamics with advanced sampling techniques
- Analyzes structural properties, composition distribution, and stability
- Output: Final stable nitinol nanoparticle structures with size distribution

## Directory Structure
```plaintext
/workspace/
├── setup_sim/                             # Main simulation directory
│   ├── data/                              # Data storage
│   │   └── phase1/                        # Phase 1 (vaporization) outputs
│   ├── docs/                              # Documentation
│   │   ├── crf_parameters.md              # Critical parameters reference
│   │   ├── project_structure.md           # Detailed project structure info
│   │   └── README.md                      # General documentation
│   ├── inputs/                            # Simulation inputs
│   │   ├── H2O.mol                        # Water molecule definition
│   │   └── Ni-Ti.eam.fs                   # EAM potential for Ni-Ti interactions
│   ├── src/                               # Source code
│   │   ├── phase1.lammps                  # Vaporization phase script
│   │   ├── phase2.lammps                  # Plasma cooling phase script
│   │   ├── phase3.lammps                  # Condensation in water script
│   │   ├── phase4.lammps                  # Coagulation phase script
│   │   ├── pipeline.sh                    # Main workflow automation script
│   │   └── py_phase4.py                   # Python analysis for phase 4
├── tests/                                 # Testing directory
│   ├── basic_visualization_code.py        # Simple visualization utilities
│   ├── module_test.py                     # Module testing code
│   ├── README.md                          # Testing documentation
│   ├── ljmelt_test/                       # Lennard-Jones melt test case
│   │   ├── in.lj.txt                      # LJ input file
│   │   ├── log.lammps                     # LAMMPS log file
│   │   └── run_lammps.sh                  # Test run script
│   └── ref_lammps_testing/                # Reference testing examples
│       ├── ref_script.lammps              # Reference LAMMPS script
│       ├── ref_testing_bash.sh            # Reference bash runner
│       └── xyzdata_Ni50.0_Ti50.0_1.0nm.data # Test data file
```

## Expected Outputs

The simulation pipeline produces several key outputs:

1. **Trajectory Data**: Atomic positions and velocities throughout all simulation phases
2. **Structural Analysis**: Radial distribution functions, cluster size distributions
3. **Thermal Properties**: Temperature profiles, heat transfer rates
4. **Composition Analysis**: Distribution of Ni and Ti within formed nanoparticles
5. **Particle Statistics**: Size distributions, morphologies, and stability metrics

## Workflow Execution

1. Initialize the simulation environment with `pipeline.sh`
2. Run sequential phases or execute specific phases independently
3. Monitor progress through log files and real-time visualization
4. Analyze results using the provided Python tools in `py_phase4.py`
5. Generate reports and visualizations for publication

## Technical Requirements

- CUDA-capable GPU with at least 6GB VRAM
- 32GB+ system RAM for larger simulations
- 100GB+ storage for trajectory data
- LAMMPS with GPU acceleration (KOKKOS package)
- Python 3.8+ with scientific packages (numpy, scipy, ase)

## Potential Models & LAMMPS Compatibility

### Currently Working Potentials
- **EAM/FS**: The `Ni-Ti.eam.fs` file included in the inputs directory is compatible with the KOKKOS-enabled LAMMPS build in our container.

### Alternative Potential Options
If you need to use other potential types with this simulation:

1. **MEAM Potentials**:
   - **Option A**: Rebuild LAMMPS container with MEAM/KK support
     ```bash
     # Example commands to rebuild LAMMPS with MEAM and KOKKOS
     cd lammps/src
     make yes-meam
     make yes-kokkos
     make kokkos_mpi_only
     ```
   - **Option B**: Convert your simulation to use EAM instead of MEAM
   - **Option C**: Use a different container with MEAM support already built

2. **Machine Learning Potentials (.pb files)**:
   - These typically require ML-IAP or similar packages to be enabled
   - Consider rebuilding your LAMMPS container with the required packages:
     ```bash
     # Example for ML-IAP support
     cd lammps/src
     make yes-ml-iaap
     make yes-kokkos
     make kokkos_mpi_only
     ```

3. **DeepMD Support**:
   - LAMMPS needs to be specially compiled with DeepMD-kit
   - This requires installation of DeepMD-kit first, then compiling LAMMPS with it
   - Example instructions can be found at: https://github.com/deepmodeling/deepmd-kit/blob/master/doc/install/install-lammps.md

### Validation References

For validating your nitinol nanoparticle formation results, consider these experimental references:

1. Kang et al. (2022), "Formation mechanisms of nitinol nanoparticles by micro-EDM process", *Journal of Materials Processing Technology*
2. Zhang et al. (2021), "Characterization of nitinol nanoparticles produced by electrical discharge in liquid media", *Materials Science and Engineering: A*
3. Liu et al. (2023), "Size-dependent properties of micro-EDM fabricated nitinol nanoparticles", *Nanomaterials*

### Reproducibility Guidelines
- LAMMPS version: 15Jun2023 patch (minimum recommended version)
- Input parameter files: stored in inputs/ with clear documentation
- Random seed handling: explicit control in all phase scripts
- Initial configuration generation: documented in setup_sim/docs/crf_parameters.md

## Recommended Parameter Sensitivity Analysis

For realistic results, consider studying the sensitivity of your simulation to these parameters:

1. **Heating Rate**: 10¹², 10¹³, and 10¹⁴ K/s in Phase 1
2. **Cooling Rate**: 10⁹, 10¹⁰, and 10¹¹ K/s in Phase 2
3. **Water Density**: 0.9, 1.0, and 1.1 g/cm³ in Phase 3
4. **System Size**: Vary between 10³, 10⁴, and 10⁵ atoms

Record these variations and their impact on:
- Final particle size distribution
- Crystallinity of formed nanoparticles
- Ni:Ti ratio in final particles
- Morphology characteristics (sphericity, surface roughness)
