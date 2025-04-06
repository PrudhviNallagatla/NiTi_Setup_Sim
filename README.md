# Nitinol NP ML Dataset Project - Reference Guide

## Project Summary

- **Purpose**: Generate ML-ready dataset of nitinol nanoparticles from micro-EDM simulations
- **Target Hardware**: GPU-accelerated computing (GTX 1650 for testing, more powerful for production)
- **Initial Validation**: 1nm size (~14 atoms) on GTX 1650
- **Final Target**: Parameter sweep of sizes 1-20nm, various compositions and conditions
- **Environment**: VS Code Dev Container with LAMMPS GPU support

## Container Setup

- **Base Image**: nvcr.io/hpc/lammps:patch_15Jun2023
- **GPU Access**: Full passthrough via "--gpus=all"
- **Python Environment**: Pre-installed scientific packages (numpy, scipy, ase, etc.)
- **LAMMPS Build**: Includes KOKKOS package for GPU acceleration
- **Development**: Full VS Code integration with extensions for Python/C++

## Directory structure
```plaintext
/home/rimuru/workspace/
├── src/                                    # Source code
│   ├── core/                               # Core simulation functionality
│   ├── analysis/                           # Analysis modules
|   ├── scripts/                            # Utility scripts
|   │   ├── data_conversion/                # Format conversion tools (.py)
|   │   ├── automation/                     # Workflow automation scripts (.py, .sh)
|   │   └── examples/                       # Educational notebooks (.ipynb)
│   └── visuals/                            # Visualization tools
|
├── data/                                   # Data directory
│   ├── atomic_models/                      # Raw Data
│   │   ├── experimental/                   # Experimental measurements
│   │   │   ├── isa_tabs/                   # ISA-TAB-Nano files (.txt, .csv)
│   │   │   └── raw_measurements/           # Raw experimental results (.csv, .json)
│   │   └── simulated_models/               # Raw simulation outputs
│   │       ├── NiXX-TiYY/                  # By composition
│   │       │   └── Znm/                    # By size (1-20nm)
│   │       │       ├── initial.xyz         # Initial configurations
│   │       │       └── meta.yml            # Structure metadata
│   ├── derivatives/                        # Processed outputs
│   │   ├── properties/                     # Calculated properties
│   │   │   ├── mechanical.parquet          # Mechanical properties data
│   │   │   └── thermal.parquet             # Thermal properties data
│   │   ├── ml_features/                    # ML-ready feature data (.npz, .h5)
│   │   └── visualization/                  # Visualization data (.vtk, .xdmf)
│   ├── meta_data/                          # Meta Data
│   │   ├── schema.jsonld                   # JSON-LD schema
│   │   ├── isa_investigation.txt           # ISA-TAB-Nano master file
│   │   ├── unf_template.json               # UNF structure template
│   │   └── validation/                     # Validation reports (.pdf, .json)
│   ├── simulations/                        # Simulation data
│       ├── NiXX-TiYY/                      # By composition
│       │   └── Znm/                        # By size (1-20nm)
│       │       ├── input.in                # LAMMPS input script
│       │       ├── trajectory.h5           # HDF5 trajectory data
│       │       └── log.lammps              # Simulation logs
|
├── docs/                                   # Documentation
│   ├── file_formats.md                     # File format specifications
│   ├── Use_cases.md                        # Use case documentation
│   ├── api/                                # API documentation (.md, .html)
│   └── tutorials/                          # User tutorials (.md, .ipynb)
|
├── tests/                                  # Test suite
│   ├── container_testing/                  # To test containers (.py, .sh)
|
├── aiml/                                   # AI/ML resources (.py, .h5, .pkl)
|
├── final_dataset/                          # Finally generated outputs and final dataset
│   ├── simulations/                        # Simulation results
│   │   ├── data/                           # Data files (.csv, .json)
│   │   ├── logs/                           # Log files (.log, .txt)
│   │   ├── trajectories/                   # Trajectory files (.h5md)
│   │   └── analysis/                       # Analysis results (.csv, .json)
│   ├── visualizations/                     # Generated visualizations
│   │   ├── static/                         # Static images (.png, .jpg)
│   │   └── interactive/                    # Interactive visualizations (.glb, .gltf)
│   └── reports/                            # Generated reports and figures (.pdf, .html)
|
├── config/                                 # Configuration files
│   ├── simulation/                         # Simulation configurations
│   │   ├── potentials/                     # Interatomic potentials (.eam, .tersoff)
│   │   ├── yaml_configs/                   # YAML configuration files (.yaml, .yml)
│   ├── analysis/                           # Analysis configurations (.yaml, .json)
|
├── .devcontainer/                          # Dev Container files
│   ├── devcontainer.json                   # vs code dev container configs
│   └── Dockerfile                          # Dockerfile
|
└── .github/                                # CI/CD configurations
    └── workflows/                          # GitHub Actions workflows (.yml)
```
