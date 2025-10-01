# Project TODO List

This document outlines planned features, improvements, and known issues for the Linux Kernel Build Project.

## High Priority

*   **Implement Kernel Compilation Logging:** Currently, the `kernel-compilation.log` captures the output of `make olddefconfig` but not the full `make` output during the actual kernel compilation. This needs to be properly redirected to `kernel-compilation.log` for detailed debugging.
*   **GPG Key Management Improvement:** While a temporary key is generated, explore options for more persistent key management for signing, such as allowing users to provide a path to a pre-existing private key with a passphrase (handled securely).
*   **Error Handling Refinement:** Enhance error reporting and recovery mechanisms, especially for Docker-related failures and unexpected build issues.

## Medium Priority

*   **Add Support for Multiple Kernel Versions:** Currently hardcoded to `6.16.8`. Implement a mechanism to easily specify and download different kernel versions.
*   **Support for Different Architectures:** Extend the build process to support other architectures beyond `x86_64`.
*   **Automated Testing:** Integrate automated tests for the build process itself (e.g., unit tests for Python scripts, integration tests for Docker builds).
*   **Configuration Validation:** Implement checks to validate the provided kernel configuration file before starting the build.

## Low Priority

*   **Performance Benchmarking Integration:** Integrate the kernel build process with the `benchmark/` tools to automatically run benchmarks on newly built kernels.
*   **CI/CD Integration:** Develop example CI/CD pipelines (e.g., GitHub Actions, GitLab CI) to automate kernel builds and testing.
*   **Documentation Expansion:** Add more detailed documentation for specific components, such as the Dockerfiles and kernel configuration options.
*   **User Interface (CLI Enhancements):** Improve the command-line interface with more options, progress indicators, and clearer output.

## Known Issues

*   None currently identified beyond those addressed in the TODO list.