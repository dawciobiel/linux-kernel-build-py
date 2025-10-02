#!/usr/bin/env python3
import argparse
import subprocess
import os
import datetime
import sys
import os

# Add the repository root to sys.path for module imports
repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
sys.path.insert(0, repo_root)

from scripts.kernel_builder import KernelBuilder

def run_command(command, cwd=None, capture_output=False, check=True, log_file=None):
    """
    Runs a shell command, optionally capturing output and writing to a log file.
    """
    print(f"Executing: {' '.join(command)}")
    if log_file:
        log_file.write(f"Executing: {' '.join(command)}\n")
        log_file.flush()

    if log_file:
        capture_output = True

    process = subprocess.run(
        command,
        cwd=cwd,
        capture_output=capture_output,
        text=True,
        check=check,
        encoding='utf-8'
    )

    if capture_output:
        if log_file:
            log_file.write(process.stdout)
            log_file.write(process.stderr)
            log_file.flush()
        return process.stdout, process.stderr
    else:
        if log_file:
            log_file.write(process.stdout)
            log_file.write(process.stderr)
            log_file.flush()
        return None, None

def main():
    parser = argparse.ArgumentParser(description="Build a custom Linux kernel RPM in a Docker container.")
    parser.add_argument("kernel_config_path", help="Path to the kernel configuration file (e.g., kernel-config/host-config/host-config.config)")
    parser.add_argument("kernel_release_suffix", nargs="?", default="", help="Optional suffix for the kernel release (e.g., my-build)")
    parser.add_argument("--make-jobs", "-j", help="Number of jobs for make. Can be an integer, \"auto\", or \"auto+1\". Default is \"auto\".", default="auto")
    args = parser.parse_args()

    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
    docker_image = "kernel-builder-py"
    build_script_in_container = "/workspace/scripts/kernel_builder.py"

    build_timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    log_dir = os.path.join(repo_root, "log", build_timestamp)
    os.makedirs(log_dir, exist_ok=True)

    log_files = {
        'kernel-build': os.path.join(log_dir, 'kernel-build.log'),
        'kernel-compilation': os.path.join(log_dir, 'kernel-compilation.log'),
        'rpm-build': os.path.join(log_dir, 'rpm-build.log'),
        'gpg-signing': os.path.join(log_dir, 'gpg-signing.log'),
    }

    # Create empty log files to ensure they exist before passing to container
    for log_path in log_files.values():
        open(log_path, 'a').close()

    with open(log_files['kernel-build'], "w", encoding='utf-8') as log_f:
        log_f.write(f">>> Build started at: {datetime.datetime.now()}\n")
        log_f.write(f">>> Kernel Config: {args.kernel_config_path}\n")
        log_f.write(f">>> Custom Suffix: {args.kernel_release_suffix}\n")
        log_f.flush()

        print(f">>> Build started at: {datetime.datetime.now()}")
        print(f">>> Kernel Config: {args.kernel_config_path}")
        print(f">>> Custom Suffix: {args.kernel_release_suffix}")

        cpu_model = "Unknown CPU"
        total_ram = "Unknown RAM"
        try:
            cpu_model = subprocess.check_output("lscpu | grep 'Model name:' | cut -d':' -f2 | xargs", shell=True, text=True).strip()
            total_ram = subprocess.check_output("free -h | grep Mem: | awk '{print $2}'", shell=True, text=True).strip()
        except subprocess.CalledProcessError as e:
            print(f"Warning: Could not get system info: {e}", file=sys.stderr)
            log_f.write(f"Warning: Could not get system info: {e}\n")
            log_f.flush()

        container_name = "kernel-builder-container-py"
        print(f">>> Building kernel in Docker (openSUSE Tumbleweed base)...")
        log_f.write(f">>> Building kernel in Docker (openSUSE Tumbleweed base)...\n")
        log_f.flush()

        run_command(["docker", "rm", "-f", container_name], check=False, log_file=log_f)

        start_time = datetime.datetime.now()

        docker_run_cmd = [
            "docker", "run", "-d", "--name", container_name,
            "-v", f"{repo_root}:/workspace",
            "-e", f"BUILD_TIMESTAMP={build_timestamp}",
            "-e", f"LOG_DIR={log_dir}", # Pass log_dir to the container
            docker_image,
            "tail", "-f", "/dev/null"
        ]
        run_command(docker_run_cmd, log_file=log_f)

        try:
            print(">>> Generating GPG key pair inside container...")
            log_f.write(f">>> Generating GPG key pair inside container...\n")
            log_f.flush()
            run_command(["docker", "exec", container_name, "bash", "/workspace/scripts/generate_gpg_key.sh"], log_file=open(log_files['gpg-signing'], 'a'))

            print(">>> Executing kernel_builder.py inside Docker container...")
            log_f.write(f">>> Executing kernel_builder.py inside Docker container...\n")
            log_f.flush()

            docker_exec_cmd = [
                "docker", "exec", container_name,
                "python3", build_script_in_container,
                args.kernel_config_path,
                args.kernel_release_suffix,
                "--repo-root", "/workspace",
                "--rpmbuild-root", "/root/rpmbuild",
                "--log-dir", f"/workspace/log/{build_timestamp}", # Pass log_dir in container context
                "--make-jobs", args.make_jobs
            ]
            run_command(docker_exec_cmd, log_file=log_f)

            print(">>> RPM build finished successfully.")
            log_f.write(f">>> RPM build finished successfully.\n")
            log_f.flush()

        except subprocess.CalledProcessError as e:
            print(f">>> ERROR: Kernel build failed: {e}", file=sys.stderr)
            log_f.write(f">>> ERROR: Kernel build failed: {e}\n")
            log_f.write(f"Stdout: {e.stdout}\n")
            log_f.write(f"Stderr: {e.stderr}\n")
            log_f.flush()
            sys.exit(1)
        finally:
            print(">>> Stopping and removing Docker container...")
            log_f.write(f">>> Stopping and removing Docker container...\n")
            log_f.flush()
            run_command(["docker", "stop", container_name], check=False, log_file=log_f)
            run_command(["docker", "rm", container_name], check=False, log_file=log_f)

        end_time = datetime.datetime.now()
        duration = (end_time - start_time).total_seconds()

        make_jobs_str = args.make_jobs
        if args.make_jobs == 'auto':
            make_jobs_str = f"auto ({os.cpu_count()})"
        elif args.make_jobs.startswith('auto+'):
            try:
                extra = int(args.make_jobs[5:])
                make_jobs_str = f"auto+{extra} ({os.cpu_count() + extra})"
            except ValueError:
                make_jobs_str = f"{args.make_jobs} (invalid)"

        report_file_path = os.path.join(log_dir, "report-summary.log")
        with open(report_file_path, "w", encoding='utf-8') as report_f:
            report_f.write(f"--- Kernel Build Report ---\n")
            report_f.write(f"Timestamp: {build_timestamp}\n")
            report_f.write(f"Kernel Config: {os.path.basename(args.kernel_config_path)}\n")
            report_f.write(f"Custom Suffix: {args.kernel_release_suffix if args.kernel_release_suffix else 'None'}\n")
            report_f.write(f"CPU Model: {cpu_model}\n")
            report_f.write(f"Total RAM: {total_ram}\n")
            report_f.write(f"CPU Cores for Compilation: {make_jobs_str}\n")
            report_f.write(f"Total Build Duration: {duration:.2f} seconds\n")
            report_f.write(f"Full log: {log_files['kernel-build']}\n")
            report_f.write(f"---------------------------\n")

        print(f"Build report saved to: {report_file_path}")
        log_f.write(f"Build report saved to: {report_file_path}\n")
        log_f.write(f"End date: {datetime.datetime.now()}\n")
        log_f.flush()
        print(f"End date: {datetime.datetime.now()}")

if __name__ == "__main__":
    main()
