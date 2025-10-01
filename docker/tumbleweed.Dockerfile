# Dockerfile for local kernel build (openSUSE Tumbleweed base)
FROM opensuse/tumbleweed

# Update repositories and install all required build dependencies
RUN zypper refresh && zypper dup -y && zypper install -y --allow-vendor-change --force-resolution \
        bc \
        bison \
        flex \
        gcc \
        make \
        ncurses-devel \
        perl \
        rpm \
        rpm-build \
        kernel-devel \
        xz \
        libelf-devel \
        libuuid-devel \
        libblkid-devel \
        libselinux-devel \
        zlib-devel \
        libopenssl-devel \
        libcap-devel \
        libattr-devel \
        libseccomp-devel \
        gettext-runtime \
        elfutils \
        python3 \
        python314-base \
        python314-devel \
        fakeroot \
        dwarves \
        gawk \
        rsync \
        wget \
        rpm-config-SUSE \
        kmod && \
    rm -rf /var/cache/zypp/*

RUN zypper install -y expect


# Set working directory inside container
WORKDIR /workspace

# Default command: bash shell
CMD ["/bin/bash"]

