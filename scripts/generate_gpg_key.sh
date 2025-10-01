#!/bin/bash

set -euo pipefail

# Define key details
KEY_NAME="Kernel Builder for Docker <kernel-builder-docker@example.com>"
KEY_ID="4ABB571B8AAB20B0" # Use a consistent key ID for easier management

# Generate a GPG key pair without a passphrase
# This is suitable for automated build environments where interaction is not possible.
# The key will be stored in the default GPG keyring.

# Create a batch file for non-interactive key generation
cat <<EOF > /tmp/gpg_batch_file
%echo Generating a GPG key for automated RPM signing...
Key-Type: RSA
Key-Length: 2048
Subkey-Type: RSA
Subkey-Length: 2048
Name-Real: ${KEY_NAME}
Name-Comment: Key for automated RPM signing in Docker
Name-Email: kernel-builder-docker@example.com
Expire-Date: 0
%no-protection
%commit
%echo Key generation complete.
EOF

gpg --batch --generate-key /tmp/gpg_batch_file

# Export the public key to a file that rpm can import
gpg --armor --export "${KEY_NAME}" > /workspace/RPM-GPG-KEY-docker-public.asc

# Import the public key into the RPM database
rpm --import /workspace/RPM-GPG-KEY-docker-public.asc

echo "GPG key pair generated and public key imported into RPM database."
