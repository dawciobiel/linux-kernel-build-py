#!/bin/bash

SCRIPT_DIR=$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")
bash "$SCRIPT_DIR/_build_engine" kernel-builder-py ubuntu.Dockerfile
