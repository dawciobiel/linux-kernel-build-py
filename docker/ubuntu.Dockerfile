# Dockerfile for local kernel build (Ubuntu base for SUSE-like kernel)
FROM ubuntu:latest

# Update repositories and install all required build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
        bash \
        bc \
        bison \
        flex \
        gcc \
        make \
        libncurses-dev \
        perl \
        rpm \
        tar \
        xz-utils \
        wget \
        curl \
        libelf-dev \
        uuid-dev \
        libblkid-dev \
        libselinux1-dev \
        zlib1g-dev \
        libssl-dev \
        libcap-dev \
        libattr1-dev \
        libseccomp-dev \
        gettext \
        elfutils \
        parallel \
        python3 \
        python3-dev \
        git \
        fakeroot \
        dwarves \
        gawk \
        file \
        rsync \
        openssl \
        kmod && \
    rm -rf /var/lib/apt/lists/*


# Set working directory inside container
WORKDIR /workspace

# Default command: bash shell
CMD ["/bin/bash"]
