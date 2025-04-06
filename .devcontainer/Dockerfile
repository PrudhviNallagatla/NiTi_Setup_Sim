# Use a specific tag for reproducibility
FROM nvcr.io/hpc/lammps:patch_15Jun2023

ENV TZ=Asia/Kolkata
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3-pip \
    python3-tk \
    libgl1-mesa-glx \
    libgl1-mesa-dev \
    ffmpeg \
    git \
    wget \
    curl \
    build-essential \
    nano \
    vim \
    dos2unix \
    htop \
    tmux \
    rsync \
    cmake \
    gfortran \
    nvtop \
    libhdf5-dev \
    libnetcdf-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python packages with version pins (example)
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
    tqdm==4.65.0

# Set environment variables for GPU/CPU fallback
ENV KOKKOS_DEVICES="OpenMP,Cuda"

# Create a non-root user with host-matching UID/GID
ARG USERNAME=rimuru
ARG USER_UID=1000
ARG USER_GID=$USER_UID
RUN groupadd --gid $USER_GID $USERNAME \
    && useradd --uid $USER_UID --gid $USER_GID -m $USERNAME \
    && apt-get update \
    && apt-get install -y sudo \
    && echo $USERNAME ALL=\(root\) NOPASSWD:ALL > /etc/sudoers.d/$USERNAME \
    && chmod 0440 /etc/sudoers.d/$USERNAME

# Clean up to reduce image size
RUN apt-get clean && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Set default user and workspace
USER $USERNAME
WORKDIR /home/$USERNAME
