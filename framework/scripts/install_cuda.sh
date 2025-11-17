#!/bin/bash
set -e

echo "Installing NVIDIA CUDA with custom script..."

# Install CUDA keyring with allow-downgrades flag
apt-get update
wget -O /tmp/cuda-keyring.deb https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2004/x86_64/cuda-keyring_1.0-1_all.deb
apt-get install -y --allow-downgrades /tmp/cuda-keyring.deb
rm /tmp/cuda-keyring.deb

# Install CUDA 11.8 and cuDNN
apt-get update
apt-get install -y cuda-11-8 libcudnn8=8.6.0.163-1+cuda11.8

echo "CUDA installation completed successfully!"
