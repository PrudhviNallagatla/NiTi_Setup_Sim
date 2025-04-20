# Use the latest CUDA Ubuntu image
FROM nvidia/cuda:12.3.0-devel-ubuntu22.04

ENV TZ=Asia/Kolkata
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3-pip \
    python3-dev \
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
    && rm -rf /var/lib/apt/lists/*

# Install nvtop for GPU monitoring
RUN apt-get update && apt-get install -y --no-install-recommends \
    libncurses5-dev \
    libncursesw5-dev \
    libudev-dev \
    libdrm-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/* \
    && git clone https://github.com/Syllo/nvtop.git \
    && mkdir -p nvtop/build && cd nvtop/build \
    && cmake .. -DNVML_RETRIEVE_HEADER_ONLINE=True \
    && make -j$(nproc) \
    && make install \
    && cd / && rm -rf nvtop

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
