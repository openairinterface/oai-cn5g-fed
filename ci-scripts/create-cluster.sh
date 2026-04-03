## A script to create minikube cluster for testing helm-charts
#/bin/bash
# SPDX-License-Identifier: MIT

set -eo pipefail
if ! command -v minikube &> /dev/null
then
    echo "minikube is not installed, install it from --> https://minikube.sigs.k8s.io/docs/start/ "
    exit 1
fi
if ! command -v kubectl &> /dev/null
then
    echo "kubectl is not installed, install it from --> https://kubernetes.io/docs/tasks/tools/install-kubectl-linux/"
    exit 1
fi
configure_metallb_for_minikube() {
  # determine load balancer ingress range
  CIDR_BASE_ADDR="$(minikube ip)"
  INGRESS_FIRST_ADDR="$(echo "${CIDR_BASE_ADDR}" | awk -F'.' '{print $1,$2,$3,3}' OFS='.')"
  INGRESS_LAST_ADDR="$(echo "${CIDR_BASE_ADDR}" | awk -F'.' '{print $1,$2,$3,253}' OFS='.')"

  CONFIG_MAP="apiVersion: v1
kind: ConfigMap
metadata:
  namespace: metallb-system
  name: config
data:
  config: |
    address-pools:
    - name: default
      protocol: layer2
      addresses:
      - $INGRESS_FIRST_ADDR - $INGRESS_LAST_ADDR"

  # configure metallb ingress address range
  echo "${CONFIG_MAP}" | kubectl apply -f -
  echo "Ip-address range from $INGRESS_FIRST_ADDR to $INGRESS_LAST_ADDR for internet network or LoadBalancer"
}
#Remove a cluster if still running
minikube delete
minikube start --driver=docker --cni=bridge --extra-config=kubeadm.pod-network-cidr=10.244.0.0/16 --cpus=4 --memory=16G --addons=metallb --addons=metrics-server
sleep 20
rm -rf /tmp/multus && git clone https://github.com/k8snetworkplumbingwg/multus-cni.git /tmp/multus || true
kubectl create -f /tmp/multus/deployments/multus-daemonset.yml
sleep 40
kubectl wait --for=condition=ready pod -l app=multus -n kube-system --timeout=2m
configure_metallb_for_minikube
## Test if multus CNI is properly configured
sleep 30
kubectl create -f - <<EOF
apiVersion: "k8s.cni.cncf.io/v1"
kind: NetworkAttachmentDefinition
metadata:
  name: oai-upf-0
spec:
  config: '{
      "cniVersion": "0.3.1",
      "name":"oai-upf-0",
      "plugins": [
        {
          "type": "macvlan",
          "capabilities": { "ips": true },
          "master": "eth0",
          "mode": "bridge",
          "ipam": {
            "type": "static",
            "routes": []
          }
        }, {
          "capabilities": { "mac": true },
          "type": "tuning"
        }
      ]
    }'
---
apiVersion: "k8s.cni.cncf.io/v1"
kind: NetworkAttachmentDefinition
metadata:
  name: oai-upf-1
spec:
  config: '{
      "cniVersion": "0.3.1",
      "name":"oai-upf-1",
      "plugins": [
        {
          "type": "macvlan",
          "capabilities": { "ips": true },
          "master": "eth0",
          "mode": "bridge",
          "ipam": {
            "type": "static",
            "routes": []
          }
        }, {
          "capabilities": { "mac": true },
          "type": "tuning"
        }
      ]
    }'
---
apiVersion: "k8s.cni.cncf.io/v1"
kind: NetworkAttachmentDefinition
metadata:
  name: oai-upf-2
spec:
  config: '{
      "cniVersion": "0.3.1",
      "name":"oai-upf-2",
      "plugins": [
        {
          "type": "macvlan",
          "capabilities": { "ips": true },
          "master": "eth0",
          "mode": "bridge",
          "ipam": {
            "type": "static",
            "routes": []
          }
        }, {
          "capabilities": { "mac": true },
          "type": "tuning"
        }
      ]
    }'
---
apiVersion: v1
kind: Pod
metadata:
  name: testpod
  labels:
    app: testmultus
  annotations:
    k8s.v1.cni.cncf.io/networks: '[
        {"name": "oai-upf-0",
         "interface": "n3",
         "ips": ["10.10.5.3/24"],
         "gateway": ["10.10.5.1"]
        },
        {"name": "oai-upf-1",
         "interface": "n4",
         "ips": ["192.168.100.3/24"],
         "gateway": ["192.168.100.1"]
        },
        {"name": "oai-upf-2",
         "interface": "n6",
         "ips": ["10.20.3.3/24"],
         "gateway": ["10.20.3.1"]
        }
            ]'
spec:
  containers:
  - name: testpod
    command: ["/bin/sh", "-c", "trap : TERM INT; sleep infinity & wait"]
    image: alpine
EOF
kubectl wait --for=condition=ready pod -l app=testmultus --timeout=3m
kubectl exec -it testpod -- ifconfig n3
kubectl delete network-attachment-definitions.k8s.cni.cncf.io oai-upf-0 oai-upf-1 oai-upf-2
kubectl delete pod testpod
echo "Cluster is properly configured"
