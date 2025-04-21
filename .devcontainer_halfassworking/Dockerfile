# Use the deepmd-kit CUDA image
FROM ghcr.io/deepmodeling/deepmd-kit:devel_cu11

# Set environment variables to non-interactive and define timezone/locale
ARG DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1 \
    TZ=Asia/Kolkata \
    LANG=en_US.utf8 \
    LC_ALL=en_US.UTF-8

# Set timezone
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# Install all system dependencies, set locale, and clean up in one layer
RUN apt-get update && apt-get install -y --no-install-recommends \
    locales \
    sudo \
    vim curl wget nano dos2unix htop tmux rsync gfortran \
    python3-pip python3-dev python3-tk \
    libglib2.0-0 libgl1 libegl1 libxkbcommon0 dbus libopengl0 \
    libgl1-mesa-glx libgl1-mesa-dev \
    build-essential g++ git ccache \
    libstdc++-12-dev \
    gcc-12 \
    g++-12 \
    cpp-12 \
    openmpi-bin libopenmpi-dev \
    cmake libblas-dev liblapack-dev python3.11-venv \
    ffmpeg libfftw3-dev \
    && echo "$LANG UTF-8" >> /etc/locale.gen && locale-gen \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Create a non-root user with host-matching UID/GID and passwordless sudo
ARG USERNAME=rimuru
ARG USER_UID=1000
ARG USER_GID=$USER_UID
RUN groupadd --gid $USER_GID $USERNAME \
    && useradd --uid $USER_UID --gid $USER_GID -m $USERNAME \
    # Add user to sudo group
    && usermod -aG sudo $USERNAME \
    # Set up passwordless sudo for the user
    && echo $USERNAME ALL=\(ALL\) NOPASSWD:ALL > /etc/sudoers.d/$USERNAME \
    && chmod 0440 /etc/sudoers.d/$USERNAME

# Define Python executable from deepmd-kit
ENV DPK_PYTHON=/opt/deepmd-kit/bin/python3

# Install pip for the deepmd-kit Python and required Python packages as root
# Combine installations into one layer
RUN curl https://bootstrap.pypa.io/get-pip.py -o /tmp/get-pip.py && \
    $DPK_PYTHON /tmp/get-pip.py && \
    rm /tmp/get-pip.py && \
    $DPK_PYTHON -m pip install --no-cache-dir \
    cython \
    fitsnap3 \
    mpi4py \
    virtualenv \
    psutil \
    tabulate \
    calorine \
    # Install Kaldo last as it's from git
    && $DPK_PYTHON -m pip install --no-cache-dir git+https://github.com/nanotheorygroup/kaldo

# Set Kokkos environment variables optimized for GTX 1650 (Turing)
ENV KOKKOS_DEVICES="OpenMP,Cuda" \
    KOKKOS_ARCH="Turing75" \
    OMP_NUM_THREADS=4

# Clone, build, and install LAMMPS as root, keep source code in /lammps
# Ensure this RUN command executes as root
RUN git clone --depth 1 https://github.com/lammps/lammps.git /lammps && \
    cd /lammps && \
    # Ensure the build directory is removed if it exists
    rm -rf build && \
    mkdir build && cd build && \
    cmake ../cmake \
    -DCMAKE_CXX_COMPILER=/usr/bin/c++ \
    -DCMAKE_CXX_STANDARD=17 \
    -DCMAKE_CXX_FLAGS="-I/usr/include/c++/12 -I/usr/include/x86_64-linux-gnu/c++/12" \
    -DBUILD_SHARED_LIBS=yes \
    -DMLIAP_ENABLE_PYTHON=yes \
    -DPKG_PYTHON=yes \
    -DPKG_MANYBODY=yes \
    -DPKG_KSPACE=yes \
    -DPKG_PHONON=yes \
    -DPKG_ML-SNAP=yes \
    -DPKG_ML-IAP=yes \
    -DPKG_ML-PACE=yes \
    -DPKG_SPIN=yes \
    -DPKG_KOKKOS=yes \
    -DPKG_MEAM=yes \
    -DPKG_USER-DEEPMD=yes \
    -DDOWNLOAD_USER-DEEPMD=yes \
    -DPKG_USER-MISC=yes \
    -DPKG_TTM=yes \
    -DKokkos_ENABLE_CUDA=yes \
    -DKokkos_ARCH_${KOKKOS_ARCH}=yes \
    -DPYTHON_EXECUTABLE:FILEPATH=$DPK_PYTHON && \
    make -j 3 && \
    make install-python

# Switch to the non-root user AFTER all installations
USER $USERNAME

# Set the working directory in the user's home
WORKDIR /home/$USERNAME

# Optional: Grant user ownership of LAMMPS source if needed for modification/rebuilding
# RUN sudo chown -R $USERNAME:$USERNAME /lammps
