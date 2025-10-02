# Building Custom Linux Kernels

This document outlines the process of building custom Linux kernel RPM packages using the provided Python-based framework.

## Overview

The core of the build process is orchestrated by the `scripts/local_kernel_build.py` script. This script leverages Docker to create an isolated build environment, where the actual kernel compilation and RPM packaging take place. It supports using various kernel configuration files and allows for custom release suffixes.

## Usage

To build a custom kernel, execute the `local_kernel_build.py` script from the project root:

```bash
python3 scripts/local_kernel_build.py <KERNEL_CONFIG_PATH> [KERNEL_RELEASE_SUFFIX] [-j | --make-jobs <VALUE>]
```

*   `<KERNEL_CONFIG_PATH>`: **Required.** The path to your desired kernel configuration file, relative to the project root. Examples include `kernel-config/tiny-config/tiny.config` or `kernel-config/host-config/host-config.config`.
*   `[KERNEL_RELEASE_SUFFIX]`: **Optional.** A custom string that will be appended to the kernel release version. This is useful for distinguishing your custom builds (e.g., `my-build`, `vbox-test`). If not provided, the kernel will be built without an additional suffix.
*   `[-j | --make-jobs <VALUE>]`: **Optional.** Specifies the number of parallel jobs for the `make` command.
    *   `<VALUE>` can be:
        *   `auto` (default): Automatically uses the number of available CPU cores.
        *   `auto+1`: Uses the number of available CPU cores plus one, which can speed up builds on some systems.
        *   An integer (e.g., `4`): Specifies an exact number of jobs.
    *   If this flag is omitted, the build will default to `auto`.

### Examples

1.  **Build a tiny kernel with a custom suffix using 4 cores:**

    ```bash
    python3 scripts/local_kernel_build.py kernel-config/tiny-config/tiny.config tiny-test -j 4
    ```

2.  **Build a kernel using a host-like configuration and all available cores plus one:**

    ```bash
    python3 scripts/local_kernel_build.py kernel-config/host-config/host-config.config -j auto+1
    ```

3.  **Build a kernel with default parallelism (all available cores):**

    ```bash
    python3 scripts/local_kernel_build.py kernel-config/host-config/host-config.config
    ```

## Build Process Details

When you run the `local_kernel_build.py` script, the following steps occur:

1.  **Environment Setup:** A unique log directory is created for the current build.
2.  **Docker Container Launch:** A Docker container (`kernel-builder-py`) is launched, mounting the project directory as `/workspace`.
3.  **GPG Key Generation (inside container):** A temporary GPG key pair is generated inside the container for signing the RPMs. The public key is imported into the container's RPM database.
4.  **Kernel Build Execution (inside container):** The `scripts/kernel_builder.py` script is executed inside the Docker container. This script performs:
    *   Setting up the `rpmbuild` environment.
    *   Downloading the kernel source tarball (if not already present in `kernel-sources/`).
    *   Extracting the kernel source.
    *   Copying the specified kernel configuration (`.config`) and running `make olddefconfig`.
    *   Generating the `kernel.spec` file dynamically.
    *   Executing `rpmbuild` to compile the kernel and package it into RPMs.
    *   Signing the generated RPMs using the GPG key generated in step 3.
5.  **Artifact Collection:** The generated RPM packages are copied from the container's `rpmbuild` directory to the host's `artifacts/rpms` directory within your project.
6.  **Cleanup:** The temporary `rpmbuild` directory inside the container is removed, and the Docker container is stopped and removed.
7.  **Reporting:** A build report (`report-summary.log`) is generated in the build's log directory, summarizing the process and system information.

## Output and Logs

Each build generates a timestamped directory under `log/` in your project root (e.g., `log/YYYYMMDD_HHMMSS`). This directory contains:

*   `kernel-build.log`: Main log for the overall build process.
*   `kernel-compilation.log`: Detailed output from the kernel compilation (`make`) stage.
*   `rpm-build.log`: Detailed output from the RPM packaging (`rpmbuild`) stage.
*   `gpg-signing.log`: Logs related to GPG key generation and RPM signing.
*   `report-summary.log`: A concise summary of the build, including duration and system info.

## Troubleshooting

*   **Docker Issues:** Ensure Docker is running and your user has the necessary permissions. Check the `kernel-build.log` for Docker-related errors.
*   **Build Failures:** Examine `kernel-compilation.log` and `rpm-build.log` for specific errors during kernel compilation or RPM packaging.
*   **Signing Issues:** Refer to `gpg-signing.log` if you encounter problems with RPM signing.
