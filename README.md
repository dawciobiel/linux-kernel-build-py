# Linux Kernel Build Project (Python)

This project provides a Python-based framework for building custom Linux kernel RPM packages within a Dockerized environment. It aims to streamline the process of kernel compilation, packaging, and signing, offering a modular and reproducible build system.

## Features

*   **Dockerized Builds:** Kernel compilation and RPM packaging occur within isolated Docker containers, ensuring consistent build environments.
*   **Python-driven Automation:** All build steps are orchestrated using Python scripts, enhancing flexibility and maintainability.
*   **Custom Kernel Configurations:** Easily build kernels with various configurations (e.g., `tiny-config`, `vbox-config-slim`).
*   **RPM Package Generation:** Produces standard RPM packages for easy installation and management on RPM-based systems.
*   **GPG Signing:** Automatically generates a temporary GPG key pair within the build container to sign the generated RPMs, ensuring package integrity.
*   **Structured Logging:** Detailed logs for each stage of the build process are generated, aiding in troubleshooting and analysis.
*   **Build Reports:** A summary report is generated for each build, providing key information about the process.

## Project Structure

```
.
├── .gitignore
├── BUILD.md              # Detailed build instructions
├── GEMINI.md             # Gemini-specific context and instructions
├── INSTALL.md            # Installation and setup guide
├── README.md             # Project overview
├── RPM-GPG-KEY-dawciobiel # Public GPG key for RPM verification (if provided)
├── TODO.md               # Project roadmap and pending tasks
├── docker/               # Dockerfiles and scripts for building Docker images
│   ├── _build_engine
│   ├── build-tumbleweed.sh
│   ├── build-ubuntu.sh
│   ├── tumbleweed.Dockerfile
│   └── ubuntu.Dockerfile
├── kernel-config/        # Custom kernel configuration files
│   ├── amd-fx8350-lspci_k.log
│   ├── amd-fx8350-lsusb.log
│   ├── README.md
│   ├── host-config/
│   ├── host-config-slim/
│   ├── tiny-config/
│   ├── vbox-config/
│   └── vbox-config-slim/
├── kernel-sources/       # Directory for kernel source tarballs
│   └── linux-6.16.8.tar.xz
└── scripts/              # Python and shell scripts for build automation
    ├── generate_gpg_key.sh
    ├── kernel_builder.py
    └── local_kernel_build.py
```

## Getting Started

Refer to `INSTALL.md` for detailed instructions on setting up the project and `BUILD.md` for how to build your first custom kernel.
