# Base image with CUDA support
FROM nvidia/cuda:12.0.1-devel-ubuntu22.04 as builder

# Set timezone
ENV TZ=Asia/Kolkata
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# Install essential build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    git \
    cmake \
    mpich \
    libmpich-dev \
    wget \
    gfortran \
    fftw3-dev \
    libfftw3-dev \
    libjpeg-dev \
    libpng-dev \
    libblas-dev \
    liblapack-dev \
    libhdf5-dev \
    libnetcdf-dev \
    python3-dev \
    python3-pip \
    zlib1g-dev \
    libz-dev \
    libzstd-dev \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install Python packages needed for build
RUN pip3 install --no-cache-dir \
    numpy \
    mpi4py

# Set environment variables for installation
ENV LAMMPS_ROOT=/opt/lammps
ENV KOKKOS_ROOT=/opt/kokkos
ENV PATH=$PATH:/opt/lammps/bin

# Clone KOKKOS for advanced GPU support
WORKDIR /opt
RUN git clone --depth 1 --branch 3.7.00 https://github.com/kokkos/kokkos.git ${KOKKOS_ROOT}

# Install DeepMD-kit for .pb file support
WORKDIR /opt
RUN git clone --recursive https://github.com/deepmodeling/deepmd-kit.git deepmd-kit
WORKDIR /opt/deepmd-kit
RUN mkdir build && cd build && \
    cmake -DCMAKE_INSTALL_PREFIX=/usr/local \
    -DFFTW_ROOT=/usr \
    -DUSE_CUDA_TOOLKIT=ON \
    -DCMAKE_CXX_FLAGS="-O3" .. && \
    make -j$(nproc) && \
    make install

# Clone LAMMPS
WORKDIR /opt
RUN git clone --depth 1 --branch stable_23Jun2022 https://github.com/lammps/lammps.git ${LAMMPS_ROOT}

# Copy DeepMD-kit to LAMMPS plugin
RUN mkdir -p ${LAMMPS_ROOT}/lib/deepmd
WORKDIR ${LAMMPS_ROOT}/lib/deepmd
RUN cp -r /opt/deepmd-kit/source/build/include . && \
    cp -r /opt/deepmd-kit/source/build/lib . && \
    cp -r /opt/deepmd-kit/source/build/bin . && \
    cp -r /opt/deepmd-kit/source/lib/include/* ./include/ && \
    ln -s /usr/local/lib/lib* ./lib/ && \
    touch ./lib/libdeepmd_c.so && \
    touch ./lib/libdeepmd_cc.so && \
    touch ./lib/libdeepmd.so

# Create build directory
WORKDIR ${LAMMPS_ROOT}/build
RUN mkdir -p ${LAMMPS_ROOT}/build

# Configure LAMMPS with CMake
RUN cmake ../cmake \
    -DCMAKE_BUILD_TYPE=Release \
    -DBUILD_SHARED_LIBS=yes \
    -DLAMMPS_MACHINE=custom \
    \
    -DPKG_ASPHERE=yes \
    -DPKG_BODY=yes \
    -DPKG_CLASS2=yes \
    -DPKG_COLLOID=yes \
    -DPKG_COMPRESS=yes \
    -DPKG_CORESHELL=yes \
    -DPKG_DIPOLE=yes \
    -DPKG_GRANULAR=yes \
    -DPKG_KSPACE=yes \
    -DPKG_MANYBODY=yes \
    -DPKG_MC=yes \
    -DPKG_MEAM=yes \
    -DPKG_MISC=yes \
    -DPKG_MOLECULE=yes \
    -DPKG_MPIIO=yes \
    -DPKG_OPT=yes \
    -DPKG_PERI=yes \
    -DPKG_PYTHON=yes \
    -DPKG_QEQ=yes \
    -DPKG_REPLICA=yes \
    -DPKG_RIGID=yes \
    -DPKG_SHOCK=yes \
    -DPKG_ML-IAP=yes \
    -DPKG_ML-PACE=yes \
    -DPKG_ML-SNAP=yes \
    -DPKG_USER-DEEPMD=yes \
    \
    -DKokkos_ENABLE_CUDA=yes \
    -DKokkos_ENABLE_OPENMP=yes \
    -DKokkos_ARCH_AMPERE80=yes \
    -DKokkos_ARCH_TURING75=yes \
    -DKokkos_ARCH_VOLTA70=yes \
    -DKokkos_ARCH_PASCAL60=yes \
    -DKokkos_ARCH_HOPPER90=yes \
    -DKokkos_ARCH_ADA89=yes \
    -DKokkos_ENABLE_CUDA_LAMBDA=yes \
    -DCMAKE_INSTALL_PREFIX=/usr/local \
    -DCMAKE_LIBRARY_PATH=/usr/local/cuda/lib64/stubs \
    -DDEEPMD_ROOT=/usr/local

# Build and install LAMMPS
RUN make -j$(nproc) && make install

# Add MEAM library
WORKDIR ${LAMMPS_ROOT}/src/MEAM
RUN make -j$(nproc) -f Makefile.mpi

# Create a runtime image with minimal dependencies
FROM nvidia/cuda:12.0.1-runtime-ubuntu22.04

# Set timezone
ENV TZ=Asia/Kolkata
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3-pip \
    python3-tk \
    libgl1-mesa-glx \
    libgl1-mesa-dev \
    ffmpeg \
    mpich \
    git \
    wget \
    curl \
    nano \
    vim \
    dos2unix \
    htop \
    tmux \
    rsync \
    nvtop \
    libhdf5-dev \
    libnetcdf-dev \
    libfftw3-3 \
    libjpeg8 \
    sudo \
    && rm -rf /var/lib/apt/lists/*

# Install Python packages
RUN pip3 install --no-cache-dir \
    numpy==1.24.3 \
    scipy==1.10.1 \
    matplotlib==3.7.1 \
    pandas==2.0.3 \
    ase==3.22.1 \
    ovito==3.9.1 \
    freud-analysis==2.12.0 \
    jupyter==1.0.0 \
    ipykernel==6.24.0 \
    scikit-learn==1.3.0 \
    pyyaml==6.0.1 \
    tqdm==4.65.0 \
    h5py==3.9.0 \
    mpi4py==3.1.4 \
    deepmd-kit==2.2.5 \
    Flask==2.3.2 \
    Flask-SocketIO==5.3.4 \
    eventlet==0.33.3 \
    qrcode[pil]==7.4.2

# Create a non-root user with host-matching UID/GID
ARG USERNAME=rimuru
ARG USER_UID=1000
ARG USER_GID=$USER_UID
RUN groupadd --gid $USER_GID $USERNAME \
    && useradd --uid $USER_UID --gid $USER_GID -m $USERNAME \
    && echo $USERNAME ALL=\(root\) NOPASSWD:ALL > /etc/sudoers.d/$USERNAME \
    && chmod 0440 /etc/sudoers.d/$USERNAME

# Copy LAMMPS installation from builder image
COPY --from=builder /usr/local /usr/local
COPY --from=builder /opt/lammps/src/MEAM/libmeam.so /usr/local/lib/

# Create directories for simulations and potential files
RUN mkdir -p /opt/scripts /opt/potentials && \
    chown -R ${USERNAME}:${USERNAME} /opt/scripts /opt/potentials

# Add GPU detection script
RUN echo '#!/bin/bash\n\
    # GPU detection script\n\
    GPU_COUNT=$(nvidia-smi --list-gpus | wc -l 2>/dev/null || echo "0")\n\
    GPU_NAME=$(nvidia-smi --query-gpu=name --format=csv,noheader | head -n 1 2>/dev/null || echo "Unknown")\n\
    \n\
    echo "Detected ${GPU_COUNT} GPUs: ${GPU_NAME}"\n\
    \n\
    # Export optimal settings based on detected GPU\n\
    if [[ "${GPU_NAME}" == *"RTX 50"* ]] || [[ "${GPU_NAME}" == *"H100"* ]]; then\n\
    export KOKKOS_ARCH=HOPPER90\n\
    echo "Using Hopper architecture settings for RTX 50 series"\n\
    elif [[ "${GPU_NAME}" == *"RTX 40"* ]] || [[ "${GPU_NAME}" == *"L40"* ]]; then\n\
    export KOKKOS_ARCH=ADA89\n\
    echo "Using Ada architecture settings for RTX 40 series"\n\
    elif [[ "${GPU_NAME}" == *"A100"* ]] || [[ "${GPU_NAME}" == *"RTX 30"* ]]; then\n\
    export KOKKOS_ARCH=AMPERE80\n\
    echo "Using Ampere architecture settings"\n\
    elif [[ "${GPU_NAME}" == *"RTX 20"* ]] || [[ "${GPU_NAME}" == *"RTX 16"* ]]; then\n\
    export KOKKOS_ARCH=TURING75\n\
    echo "Using Turing architecture settings"\n\
    elif [[ "${GPU_NAME}" == *"V100"* ]]; then\n\
    export KOKKOS_ARCH=VOLTA70\n\
    echo "Using Volta architecture settings"\n\
    elif [[ "${GPU_NAME}" == *"P100"* ]] || [[ "${GPU_NAME}" == *"GTX 10"* ]]; then\n\
    export KOKKOS_ARCH=PASCAL60\n\
    echo "Using Pascal architecture settings"\n\
    elif [[ "${GPU_COUNT}" == "0" ]]; then\n\
    echo "No GPU detected, using CPU-only mode"\n\
    export KOKKOS_DEVICES="OpenMP"\n\
    else\n\
    # Default to a safe option\n\
    export KOKKOS_ARCH=PASCAL60\n\
    echo "Using default Pascal architecture settings"\n\
    fi\n\
    \n\
    # Apply optimizations based on detected architecture\n\
    export OMP_NUM_THREADS=4\n\
    export LAMMPS_POTENTIALS=/opt/potentials\n\
    \n\
    # Print summary of environmental settings\n\
    echo "Environment configured:"\n\
    echo " - KOKKOS_ARCH: ${KOKKOS_ARCH:-Not set}"\n\
    echo " - KOKKOS_DEVICES: ${KOKKOS_DEVICES:-Cuda,OpenMP}"\n\
    echo " - OMP_NUM_THREADS: ${OMP_NUM_THREADS}"\n' > /opt/scripts/detect_gpu.sh && \
    chmod +x /opt/scripts/detect_gpu.sh

# Add an info script to validate potential formats
RUN echo '#!/bin/bash\n\
    # LAMMPS potentials support verification\n\
    echo "Checking LAMMPS package and potential support..."\n\
    \n\
    if [[ -f /usr/local/lib/libmeam.so ]]; then\n\
    echo "✓ MEAM potential support is available"\n\
    else\n\
    echo "✗ MEAM potential support is not available"\n\
    fi\n\
    \n\
    # Check for DeepMD support\n\
    if lmp -h | grep -q USER-DEEPMD; then\n\
    echo "✓ DeepMD support is available (.pb files)"\n\
    else\n\
    echo "✗ DeepMD support is not available"\n\
    fi\n\
    \n\
    # Check for ML-IAP support\n\
    if lmp -h | grep -q ML-IAP; then\n\
    echo "✓ ML-IAP support is available"\n\
    else\n\
    echo "✗ ML-IAP support is not available"\n\
    fi\n\
    \n\
    LAMMPS_PACKAGES=$(lmp -h | grep -i "Installed packages" -A 30)\n\
    echo ""\n\
    echo "Installed LAMMPS packages:"\n\
    echo "$LAMMPS_PACKAGES"\n\
    \n\
    echo ""\n\
    echo "KOKKOS GPU capabilities:"\n\
    lmp -k on g 1 -h | grep -i kokkos\n\
    \n\
    echo ""\n\
    echo "Testing .pb file support:"\n\
    if [[ -d /opt/potentials ]]; then\n\
    if ls /opt/potentials/*.pb 1> /dev/null 2>&1; then\n\
    echo "Found .pb files in /opt/potentials:"\n\
    ls -lh /opt/potentials/*.pb\n\
    else\n\
    echo "No .pb files found in /opt/potentials yet"\n\
    echo "Please copy your .pb files to /opt/potentials"\n\
    fi\n\
    fi\n' > /opt/scripts/check_potentials.sh && \
    chmod +x /opt/scripts/check_potentials.sh && \
    chown ${USERNAME}:${USERNAME} /opt/scripts/check_potentials.sh

# Add a script to copy example potential files
RUN echo '#!/bin/bash\n\
    echo "Copying NiTi potential files to /opt/potentials..."\n\
    \n\
    if [[ -d /home/rimuru/workspace/setup_sim/inputs ]]; then\n\
    if ls /home/rimuru/workspace/setup_sim/inputs/*.eam.fs 1> /dev/null 2>&1; then\n\
    cp /home/rimuru/workspace/setup_sim/inputs/*.eam.fs /opt/potentials/\n\
    echo "✓ Copied EAM files to /opt/potentials:"\n\
    ls -lh /opt/potentials/*.eam.fs\n\
    else\n\
    echo "✗ No EAM files found in workspace/setup_sim/inputs"\n\
    fi\n\
    \n\
    if ls /home/rimuru/workspace/setup_sim/inputs/*.pb 1> /dev/null 2>&1; then\n\
    cp /home/rimuru/workspace/setup_sim/inputs/*.pb /opt/potentials/\n\
    echo "✓ Copied .pb files to /opt/potentials:"\n\
    ls -lh /opt/potentials/*.pb\n\
    else\n\
    echo "✗ No .pb files found in workspace/setup_sim/inputs"\n\
    fi\n\
    else\n\
    echo "✗ Could not find workspace/setup_sim/inputs directory"\n\
    fi\n' > /opt/scripts/copy_potentials.sh && \
    chmod +x /opt/scripts/copy_potentials.sh && \
    chown ${USERNAME}:${USERNAME} /opt/scripts/copy_potentials.sh

# Add script to fix line endings
RUN echo '#!/bin/bash\n\
    echo "Fixing line endings for all scripts in the workspace..."\n\
    \n\
    if [[ -d /home/rimuru/workspace ]]; then\n\
    # Fix specific script paths in your workspace structure\n\
    for script_path in \
    "/home/rimuru/workspace/setup_sim/src/pipeline.sh" \
    "/home/rimuru/workspace/setup_sim/src/py_phase4.py" \
    "/home/rimuru/workspace/setup_sim/src/phase1.lammps" \
    "/home/rimuru/workspace/setup_sim/src/phase2.lammps" \
    "/home/rimuru/workspace/setup_sim/src/phase3.lammps" \
    "/home/rimuru/workspace/setup_sim/src/phase4.lammps" \
    "/home/rimuru/workspace/tests/basic_visualization_code.py" \
    "/home/rimuru/workspace/tests/module_test.py" \
    "/home/rimuru/workspace/tests/ljmelt_test/run_lammps.sh" \
    "/home/rimuru/workspace/tests/ref_lammps_testing/ref_testing_bash.sh"\n\
    do\n\
    if [[ -f "$script_path" ]]; then\n\
    echo "  Converting: $script_path"\n\
    dos2unix "$script_path"\n\
    \n\
    # Make shell scripts executable\n\
    if [[ "$script_path" == *.sh ]]; then\n\
    chmod +x "$script_path"\n\
    echo "  Made executable: $script_path"\n\
    fi\n\
    else\n\
    echo "  Not found: $script_path"\n\
    fi\n\
    done\n\
    \n\
    # Also convert any other scripts in the workspace by extension\n\
    echo "Checking for additional scripts by extension..."\n\
    find /home/rimuru/workspace -type f -name "*.sh" -exec dos2unix {} \\; -exec chmod +x {} \\;\n\
    find /home/rimuru/workspace -type f -name "*.py" -exec dos2unix {} \\;\n\
    find /home/rimuru/workspace -type f -name "*.lammps" -exec dos2unix {} \\;\n\
    \n\
    echo "Line ending conversion complete."\n\
    else\n\
    echo "Workspace directory not found!"\n\
    fi\n' > /opt/scripts/fix_line_endings.sh && \
    chmod +x /opt/scripts/fix_line_endings.sh && \
    chown ${USERNAME}:${USERNAME} /opt/scripts/fix_line_endings.sh

# Add script to start monitoring dashboard with remote access
RUN echo '#!/bin/bash\n\
    echo "Starting NiTi Nanoparticle Simulation Dashboard..."\n\
    \n\
    # Install ngrok if needed (will be done automatically by the dashboard script)\n\
    \n\
    # Display information on how to access the dashboard\n\
    echo ""\n\
    echo "============================================================"\n\
    echo "NiTi Simulation Dashboard starting..."\n\
    echo "The dashboard will be accessible:"\n\
    echo " - On your local network"\n\
    echo " - Remotely from any other network (via ngrok)"\n\
    echo ""\n\
    echo "A URL will be displayed shortly that you can access from anywhere."\n\
    echo "============================================================"\n\
    echo ""\n\
    \n\
    # Check if dashboard.py exists\n\
    if [ -f "/home/rimuru/workspace/setup_sim/src/dashboard.py" ]; then\n\
    cd /home/rimuru/workspace/setup_sim/src\n\
    python3 dashboard.py\n\
    else\n\
    echo "Error: dashboard.py not found in /home/rimuru/workspace/setup_sim/src/"\n\
    echo "Please make sure the file exists and the workspace is mounted correctly."\n\
    exit 1\n\
    fi\n' > /opt/scripts/start_dashboard.sh && \
    chmod +x /opt/scripts/start_dashboard.sh && \
    chown ${USERNAME}:${USERNAME} /opt/scripts/start_dashboard.sh

# Set environment variables for optimal GPU performance
ENV OMP_NUM_THREADS=4
ENV CUDA_VISIBLE_DEVICES=all
ENV KOKKOS_DEVICES="Cuda,OpenMP"
ENV LAMMPS_POTENTIALS=/opt/potentials
ENV LD_LIBRARY_PATH=/usr/local/lib:$LD_LIBRARY_PATH

# Clean up
RUN apt-get clean && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Set default user and workspace
USER $USERNAME
WORKDIR /home/$USERNAME

# Add scripts to bashrc for automatic execution
RUN echo 'source /opt/scripts/detect_gpu.sh' >> ~/.bashrc && \
    echo 'alias check-potentials="/opt/scripts/check_potentials.sh"' >> ~/.bashrc && \
    echo 'alias setup-potentials="/opt/scripts/copy_potentials.sh"' >> ~/.bashrc && \
    echo 'alias fix-scripts="/opt/scripts/fix_line_endings.sh"' >> ~/.bashrc && \
    echo 'alias monitor="/opt/scripts/start_dashboard.sh"' >> ~/.bashrc && \
    echo 'echo "💧 Welcome to NiTi Nanoparticle Simulation Environment"' >> ~/.bashrc && \
    echo 'echo " - Run \"setup-potentials\" to copy potential files from your workspace"' >> ~/.bashrc && \
    echo 'echo " - Run \"check-potentials\" to verify potential file support"' >> ~/.bashrc && \
    echo 'echo " - Run \"fix-scripts\" to convert line endings in your scripts"' >> ~/.bashrc && \
    echo 'echo " - Run \"monitor\" to start the mobile monitoring dashboard"' >> ~/.bashrc
