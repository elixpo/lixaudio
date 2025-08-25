#!/bin/bash
set -e

# -----------------------------
# 1. Detect distribution
# -----------------------------
echo "Detecting Linux distribution..."
DISTRO=$(. /etc/os-release; echo $ID$VERSION_ID)
echo "Detected distribution: $DISTRO"

# -----------------------------
# 2. Install NVIDIA Container Toolkit
# -----------------------------
echo "Adding NVIDIA GPG key and repository..."
sudo mkdir -p /etc/apt/keyrings
curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | sudo tee /etc/apt/keyrings/nvidia-container-toolkit.asc > /dev/null
echo "deb [signed-by=/etc/apt/keyrings/nvidia-container-toolkit.asc] https://nvidia.github.io/libnvidia-container/stable/deb/ubuntu2204/amd64 /" | \
    sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list > /dev/null

echo "Updating package index..."
sudo apt-get update

echo "Installing nvidia-container-toolkit..."
sudo apt-get install -y nvidia-container-toolkit

echo "Configuring containerd for NVIDIA runtime..."
sudo nvidia-ctk runtime configure --runtime=containerd
sudo systemctl restart containerd

# -----------------------------
# 3. Deploy NVIDIA Device Plugin
# -----------------------------
echo "Deploying NVIDIA device plugin for Kubernetes..."
kubectl apply -f https://raw.githubusercontent.com/NVIDIA/k8s-device-plugin/v0.17.3/nvidia-device-plugin.yml

echo "Waiting 10s for NVIDIA plugin pods to come up..."
sleep 10
kubectl get pods -n kube-system | grep nvidia

# -----------------------------
# 4. Optional: Restart audio-pollinations deployment
# -----------------------------
read -p "Do you want to restart your audio-pollinations deployment? (y/n): " RESTART
if [[ "$RESTART" == "y" ]]; then
    kubectl rollout restart deployment audio-pollinations
    echo "Deployment restarted. Checking pods..."
    kubectl get pods -o wide
fi

echo "Setup complete! You can now verify GPUs in pods using:"
echo "kubectl exec -it <pod-name> -- nvidia-smi"
