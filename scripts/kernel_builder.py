import argparse
import subprocess
import os
import datetime
import sys
import re
import glob
import logging

class KernelBuilder:
    def __init__(self, kernel_version, make_jobs, repo_root, rpmbuild_root,
                 kernel_config_path, custom_kernel_release_suffix,
                 log_dir, log_files):
        self.kernel_version = kernel_version
        self.make_jobs = make_jobs
        self.repo_root = repo_root
        self.rpmbuild_root = rpmbuild_root
        self.kernel_config_path = kernel_config_path
        self.custom_kernel_release_suffix = custom_kernel_release_suffix
        self.log_dir = log_dir
        self.log_files = log_files
        self.loggers = {}
        self._setup_logging()

        self.kernel_tar = f"linux-{self.kernel_version}.tar.xz"
        self.kernel_build_dir = os.path.join(self.rpmbuild_root, "BUILD", f"linux-{self.kernel_version}")
        self.rpm_spec_path = os.path.join(self.rpmbuild_root, "SPECS", "kernel.spec")
        self.artifacts_rpms_dir = os.path.join(self.repo_root, "artifacts", "rpms")
        self.gpg_name = "Kernel Builder for Docker <kernel-builder-docker@example.com>"

    def _setup_logging(self):
        log_format = '%(asctime)s - %(levelname)s - %(message)s'
        date_format = '%Y-%m-%d %H:%M:%S'

        # Console logger
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(logging.Formatter(log_format, datefmt=date_format))
        
        # Main logger for general build messages
        main_logger = logging.getLogger('kernel-build')
        main_logger.setLevel(logging.INFO)
        main_logger.addHandler(console_handler)
        file_handler = logging.FileHandler(self.log_files['kernel-build'])
        file_handler.setFormatter(logging.Formatter(log_format, datefmt=date_format))
        main_logger.addHandler(file_handler)
        self.loggers['kernel-build'] = main_logger

        # Specific loggers for detailed output
        for log_name, log_path in self.log_files.items():
            if log_name == 'kernel-build':
                continue
            logger = logging.getLogger(log_name)
            logger.setLevel(logging.INFO)
            file_handler = logging.FileHandler(log_path)
            file_handler.setFormatter(logging.Formatter(log_format, datefmt=date_format))
            logger.addHandler(file_handler)
            self.loggers[log_name] = logger

    def _log(self, message, level='info', logger_name='kernel-build'):
        logger = self.loggers.get(logger_name, self.loggers['kernel-build'])
        if level == 'info':
            logger.info(message)
        elif level == 'warning':
            logger.warning(message)
        elif level == 'error':
            logger.error(message)
        elif level == 'debug':
            logger.debug(message)

    def _run_command(self, command, cwd=None, capture_output=False, check=True, logger_name='kernel-build'):
        self._log(f"Executing: {' '.join(command)}", logger_name=logger_name)
        
        process = subprocess.run(
            command,
            cwd=cwd,
            capture_output=True, # Always capture output to log it
            text=True,
            check=False, # Don't raise CalledProcessError immediately, handle it below
            encoding='utf-8'
        )

        if process.stdout:
            self._log(process.stdout.strip(), logger_name=logger_name)
        if process.stderr:
            self._log(process.stderr.strip(), level='error', logger_name=logger_name)

        if check and process.returncode != 0:
            self._log(f"Command failed with exit code {process.returncode}", level='error', logger_name=logger_name)
            raise subprocess.CalledProcessError(process.returncode, command, process.stdout, process.stderr)
        
        return process.stdout, process.stderr

    def _setup_rpmbuild_environment(self):
        self._log("Setting up rpmbuild environment...")
        for subdir in ["BUILD", "BUILDROOT", "RPMS", "SOURCES", "SPECS", "SRPMS"]:
            os.makedirs(os.path.join(self.rpmbuild_root, subdir), exist_ok=True)
        self._log("rpmbuild environment setup complete.")

    def _download_and_extract_kernel_source(self):
        self._log("Ensuring kernel source tarball is available...")
        kernel_sources_path = os.path.join(self.repo_root, "kernel-sources")
        os.makedirs(kernel_sources_path, exist_ok=True)
        
        if not os.path.exists(os.path.join(kernel_sources_path, self.kernel_tar)):
            self._log(f"Downloading kernel source: {self.kernel_tar}...")
            self._run_command(["wget", f"https://cdn.kernel.org/pub/linux/kernel/v6.x/{self.kernel_tar}", "-O", os.path.join(kernel_sources_path, self.kernel_tar)])
        
        self._run_command(["cp", os.path.join(kernel_sources_path, self.kernel_tar), os.path.join(self.rpmbuild_root, "SOURCES/")])
        self._log("Extracting kernel source...")
        self._run_command(["tar", "-xf", os.path.join(self.rpmbuild_root, "SOURCES", self.kernel_tar)], cwd=os.path.join(self.rpmbuild_root, "BUILD"))
        self._log("Kernel source extracted.")

    def _prepare_kernel_config(self):
        self._log("Preparing kernel configuration...")
        os.makedirs(self.kernel_build_dir, exist_ok=True)
        self._run_command(["cp", os.path.join(self.repo_root, self.kernel_config_path), os.path.join(self.kernel_build_dir, ".config")])
        self._run_command(["make", "olddefconfig"], cwd=self.kernel_build_dir)
        self._log("Kernel configuration prepared.")

    def _generate_spec_file(self):
        self._log("Generating dynamic .spec file...", logger_name='kernel-build')

        # Determine final kernel release string
        final_kernel_release_output, _ = self._run_command(
            ["make", "-s", "kernelrelease", f"LOCALVERSION=-{self.custom_kernel_release_suffix}"],
            cwd=self.kernel_build_dir,
            capture_output=True,
            logger_name='kernel-build'
        )
        final_kernel_release = final_kernel_release_output.strip()
        rpm_release_string = final_kernel_release.replace(f"{self.kernel_version}-", "").replace("-", ".")

        self._log(f"Final kernel release string (for uname -r): {final_kernel_release}", logger_name='kernel-build')
        self._log(f"RPM Release string (for spec file): {rpm_release_string}", logger_name='kernel-build')

        spec_content = f"""
# Global definitions
%global final_krelease {final_kernel_release}
%global custom_suffix {self.custom_kernel_release_suffix}
%global _build_id_links %{{nil}}

# --- Main Package (kernel) ---
Name:           kernel
Version:        {self.kernel_version}
Release:        {rpm_release_string}
Summary:        Custom kernel for this project
License:        GPLv2
Group:          System/Kernel
Source0:        {self.kernel_tar}
# Using the more comprehensive list of build dependencies from the old CI script
BuildRequires:  bc, rsync, openssl, openssl-devel, elfutils, rpm-build, dwarves, \
                bison, flex, gcc, make, ncurses-devel, perl, xz, \
                libelf-devel, libuuid-devel, libblkid-devel, libselinux-devel, \
                zlib-devel, libopenssl-devel, libcap-devel, libattr-devel, \
                libseccomp-devel, gettext-runtime, python3, python314-devel, \
                fakeroot, gawk, file, kmod, gnupg

%define _gpg_name Linux Kernel Builder by dawciobiel <dawciobiel@gmail.com>
%global _signature gpg

%description
Custom kernel for this project (%{{final_krelease}}).

# --- Sub-package for modules ---
%package modules
Summary:        Kernel modules for the custom kernel
Group:          System/Kernel
Requires:       kernel = %{{version}}-%{{release}}
Provides:       kernel-modules = %{{version}}-%{{release}}

%description modules
Kernel modules for the custom kernel (%{{final_krelease}}).

# --- Sub-package for devel ---
%package devel
Summary:        Development headers for the custom kernel
Group:          System/Kernel
Requires:       kernel = %{{version}}-%{{release}}

%description devel
Development headers and files for building modules against the custom kernel (%{{final_krelease}}).

# --- Build Process ---
%prep
%setup -q -n linux-%{{version}}
cp "{self.repo_root}/{self.kernel_config_path}" .config
make olddefconfig

%build
make -j{self.make_jobs} LOCALVERSION=-%{{custom_suffix}}
make modules_prepare

%install
# Install kernel
mkdir -p %{{buildroot}}/boot
cp -v arch/x86/boot/bzImage %{{buildroot}}/boot/vmlinuz-%{{final_krelease}}
cp -v System.map %{{buildroot}}/boot/System.map-%{{final_krelease}}
cp -v .config %{{buildroot}}/boot/config-%{{final_krelease}}

# Install modules
make modules_install INSTALL_MOD_PATH=%{{buildroot}} KERNELRELEASE=%{{final_krelease}} DEPMOD=/bin/true

# --- File Definitions ---
%files
/boot/vmlinuz-%{{final_krelease}}
/boot/System.map-%{{final_krelease}}
/boot/config-%{{final_krelease}}

%files modules
# Corrected path for modules
/lib/modules/%{{final_krelease}}/

%files devel
/lib/modules/%{{final_krelease}}/build

%changelog
* {datetime.datetime.now().strftime("%a %b %d %Y")} User - %{{version}}-%{{release}}
- Automated RPM build.
"""
        with open(self.rpm_spec_path, "w", encoding='utf-8') as f:
            f.write(spec_content)
        self._log(f"Generated .spec file at: {self.rpm_spec_path}", logger_name='kernel-build')

        return final_kernel_release # Return this for later use in install

    def _run_rpm_build(self):
        self._log("Starting RPM build...", logger_name='kernel-build')
        rpmbuild_cmd = [
            "rpmbuild", "-bb", "-vv",
            "--define", f"_topdir {self.rpmbuild_root}",
            "--noclean",
            self.rpm_spec_path
        ]
        self._run_command(rpmbuild_cmd, logger_name='rpm-build')
        self._log("RPM build finished successfully.", logger_name='kernel-build')

    def _sign_rpms(self):
        self._log("Signing RPM packages...", logger_name='kernel-build')
        rpm_files = glob.glob(os.path.join(self.rpmbuild_root, "RPMS", "x86_64", "*.rpm"))
        if not rpm_files:
            self._log("No RPM files found to sign.", level='warning', logger_name='kernel-build')
            return

        for rpm_file in rpm_files:
            self._log(f"Signing {os.path.basename(rpm_file)}...", logger_name='kernel-build')
            self._run_command(["rpmsign", "--addsign", "--define", f"_gpg_name {self.gpg_name}", rpm_file], logger_name='gpg-signing')
        self._log("RPM packages signed successfully.", logger_name='kernel-build')

    def _copy_rpms_to_artifacts(self):
        self._log("Copying RPMs to artifacts directory...", logger_name='kernel-build')
        os.makedirs(self.artifacts_rpms_dir, exist_ok=True)
        rpm_files = glob.glob(os.path.join(self.rpmbuild_root, "RPMS", "x86_64", "*.rpm"))
        self._run_command(["cp", "-v"] + rpm_files + [self.artifacts_rpms_dir], logger_name='kernel-build')
        self._log("RPMs copied to artifacts directory.", logger_name='kernel-build')

    def _cleanup_rpmbuild_directory(self):
        self._log("Removing rpmbuild directory...", logger_name='kernel-build')
        self._run_command(["rm", "-rf", self.rpmbuild_root], logger_name='kernel-build')
        self._log("rpmbuild directory removed.", logger_name='kernel-build')

    def build(self):
        self._log("Kernel build process started.", logger_name='kernel-build')
        try:
            self._setup_rpmbuild_environment()
            self._download_and_extract_kernel_source()
            self._prepare_kernel_config()
            self._generate_spec_file()
            self._run_rpm_build()
            self._sign_rpms()
            self._copy_rpms_to_artifacts()
            self._cleanup_rpmbuild_directory()
            self._log("Kernel build process finished successfully.", logger_name='kernel-build')
        except subprocess.CalledProcessError as e:
            self._log(f"Kernel build failed: {e}", level='error', logger_name='kernel-build')
            sys.exit(1)
        except Exception as e:
            self._log(f"An unexpected error occurred: {e}", level='error', logger_name='kernel-build')
            sys.exit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Build a custom Linux kernel RPM.")
    parser.add_argument("kernel_config_path", help="Path to the kernel configuration file (e.g., kernel-config/host-config/host-config.config)")
    parser.add_argument("custom_kernel_release_suffix", nargs="?", default="", help="Optional suffix for the kernel release (e.g., my-build)")
    parser.add_argument("--repo-root", default="/workspace", help="Root of the repository inside the container.")
    parser.add_argument("--rpmbuild-root", default="/root/rpmbuild", help="Root directory for rpmbuild.")
    parser.add_argument("--log-dir", required=True, help="Directory to store log files.")
    parser.add_argument("--make-jobs", default="auto", help="Number of jobs for make. Can be an integer, \"auto\", or \"auto+1\".")
    
    args = parser.parse_args()

    # Determine the number of make jobs
    make_jobs = args.make_jobs
    if make_jobs == 'auto':
        make_jobs = str(os.cpu_count())
    elif make_jobs == 'auto+1':
        make_jobs = str(os.cpu_count() + 1)

    # Define log file paths
    log_files = {
        'kernel-build': os.path.join(args.log_dir, 'kernel-build.log'),
        'kernel-compilation': os.path.join(args.log_dir, 'kernel-compilation.log'),
        'rpm-build': os.path.join(args.log_dir, 'rpm-build.log'),
        'gpg-signing': os.path.join(args.log_dir, 'gpg-signing.log'),
        # 'report-summary' will be handled by local_kernel_build.py
    }

    builder = KernelBuilder(
        kernel_version="6.16.8",
        make_jobs=make_jobs,
        repo_root=args.repo_root,
        rpmbuild_root=args.rpmbuild_root,
        kernel_config_path=args.kernel_config_path,
        custom_kernel_release_suffix=args.custom_kernel_release_suffix,
        log_dir=args.log_dir,
        log_files=log_files
    )
    builder.build()
