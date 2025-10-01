# Installation and Setup Guide

This guide will walk you through the necessary steps to set up the Linux Kernel Build Project on your local machine.

## Prerequisites

Before you begin, ensure you have the following installed:

*   **Git:** For cloning the repository.
    ```bash
    sudo apt install git # Debian/Ubuntu
    sudo dnf install git # Fedora/RHEL
    sudo zypper install git # openSUSE
    ```
*   **Python 3.8+:** The project's automation scripts are written in Python.
    ```bash
    sudo apt install python3 python3-pip # Debian/Ubuntu
    sudo dnf install python3 python3-pip # Fedora/RHEL
    sudo zypper install python3 python3-pip # openSUSE
    ```
*   **Docker:** The kernel build process is containerized using Docker. Ensure Docker is installed and running, and your user has the necessary permissions to run Docker commands (e.g., by being part of the `docker` group).
    *   [Install Docker Engine](https://docs.docker.com/engine/install/)
    *   [Manage Docker as a non-root user](https://docs.docker.com/engine/install/linux-postinstall/#manage-docker-as-a-non-root-user)

## Setup Steps

1.  **Clone the Repository:**

    ```bash
    git clone https://github.com/dawciobiel/linux-kernel-build-py.git
    cd linux-kernel-build-py
    ```

2.  **Build the Docker Image:**

    The project uses a custom Docker image for the kernel build environment. You need to build this image once.

    For openSUSE Tumbleweed-based build environment (recommended):
    ```bash
    bash docker/build-tumbleweed.sh
    ```

    For Ubuntu-based build environment:
    ```bash
    bash docker/build-ubuntu.sh
    ```

    This will create a Docker image named `kernel-builder-py`.

3.  **Download Kernel Sources (Optional, but recommended):**

    The build script will automatically download the kernel source if it's not present. However, you can manually download it to `kernel-sources/` to speed up subsequent builds or if you prefer to manage the source manually.

    The current project is configured for Linux kernel `6.16.8`.
    ```bash
    mkdir -p kernel-sources
    wget https://cdn.kernel.org/pub/linux/kernel/v6.x/linux-6.16.8.tar.xz -O kernel-sources/linux-6.16.8.tar.xz
    ```

4.  **Prepare GPG Key for Signing (Optional, but recommended for signed RPMs):**

    The build process automatically generates a temporary GPG key pair inside the Docker container for signing RPMs. If you wish to use your own existing GPG key for signing, you would need to provide its private key file and modify the `scripts/local_kernel_build.py` to import it. For most use cases, the auto-generated key is sufficient.

    If you have an existing GPG key you want to use, ensure its public key is imported into your system's RPM database for verification purposes:
    ```bash
    sudo rpm --import /path/to/your/public-gpg-key.asc
    ```

    For this project, the `RPM-GPG-KEY-dawciobiel` file is expected to be in the project root if you want to use a pre-existing key for verification. The build script will attempt to import it into the container's RPM database.

Once these steps are completed, you are ready to build custom Linux kernels. Refer to `BUILD.md` for instructions on initiating a kernel build.
